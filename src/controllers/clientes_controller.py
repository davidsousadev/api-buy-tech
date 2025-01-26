import string
import random

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime, timedelta, timezone
from src.auth_utils import get_logged_cliente, get_logged_admin, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
from src.database import get_engine
from src.models.clientes_models import SignInClienteRequest, SignUpClienteRequest, Cliente, UpdateClienteRequest, ClienteResponse
from src.models.revendedores_models import Revendedor
from src.models.admins_models import Admin
from passlib.context import CryptContext
import jwt
from decouple import config
from davidsousa import enviar_email
from src.models.emails_models import Email
from src.html.email_confirmacao import template_confirmacao

EMAIL = config('EMAIL')
KEY_EMAIL = config('KEY_EMAIL')
URL= config('URL')

router = APIRouter()

# Gera codigo com 6 caracteres para confirmação
def gerar_codigo_confirmacao(tamanho=6):
        """Gera um código aleatório de confirmação."""
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choices(caracteres, k=tamanho))

# Lista os verbos disponiveis para esse controller
@router.options("", status_code=status.HTTP_200_OK)
async def options_clientes():
    return { "methods": ["GET", "POST", "PATCH"] }

# Endpoint para verificar duplicidade de email
@router.get("/verificar-email")
async def verificar_email(email: str):
    with Session(get_engine()) as session:
        # Verifica duplicidade em clientes
        statement = select(Cliente).where(Cliente.email == email)
        cliente = session.exec(statement).first()

        # Verifica duplicidade em admins
        statement_admin = select(Admin).where(Admin.email == email)
        admin = session.exec(statement_admin).first()

        # Verifica duplicidade em revendedores
        statement_revendedor = select(Revendedor).where(Revendedor.email == email)
        revendedor = session.exec(statement_revendedor).first()
        
        if cliente or admin or revendedor:
            raise HTTPException(status_code=400, detail="Email já cadastrado.")

    return {"message": "Email disponível."}

# Endpoint para verificar duplicidade de CPF
@router.get("/verificar-cpf")
async def verificar_cpf(cpf: str):
    with Session(get_engine()) as session:
        # Verifica duplicidade em clientes
        statement = select(Cliente).where(Cliente.cpf == cpf)
        cliente = session.exec(statement).first()

        # Verifica duplicidade em admins
        statement_admin = select(Admin).where(Admin.cpf == cpf)
        admin = session.exec(statement_admin).first()

        # Verifica duplicidade em revendedores
        statement_revendedor = select(Revendedor).where(Revendedor.cpf == cpf)
        revendedor = session.exec(statement_revendedor).first()
        
        if cliente or admin or revendedor:
            raise HTTPException(status_code=400, detail="CPF já cadastrado.")

    return {"message": "CPF disponível."}

# Listar clientes
@router.get("", response_model=list[ClienteResponse])
def listar_clientes(admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem listar usuarios."
        )

    with Session(get_engine()) as session:
        statement = select(Cliente)
        clientes = session.exec(statement).all()
        return [ClienteResponse.model_validate(u) for u in clientes]

# Administrador atualiza clientes
@router.patch("/admin/atualizar/{cliente_id}")
def atualizar_clientes_por_id(
    cliente_id: int,
    cliente_data: UpdateClienteRequest,
    admin: Annotated[Cliente, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
    
    with Session(get_engine()) as session:
        sttm = select(Cliente).where(Cliente.id == cliente_id)
        cliente_to_update = session.exec(sttm).first()

        if not cliente_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )
        
        if cliente_to_update.cod_confirmacao_email != "Confirmado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="E-mail não confirmado!"
            )

        # Atualizar os campos fornecidos
        if cliente_data.nome:
            cliente_to_update.nome = cliente_data.nome
            
        if cliente_data.email:
            # Verifica duplicidade de e-mail em Cliente
            cliente_email_query = select(Cliente).where(Cliente.email == cliente_data.email)
            if session.exec(cliente_email_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="E-mail já cadastrado por outro usuário!"
                )
            
            # Verifica duplicidade de e-mail em Admin
            admin_email_query = select(Admin).where(Admin.email == cliente_data.email)
            if session.exec(admin_email_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="E-mail já cadastrado por um administrador!"
                )

            # Atualizar o e-mail (mantendo o atual como "não confirmado")
            cliente_to_update.cod_confirmacao_email = cliente_to_update.email
            cliente_to_update.email = cliente_data.email

        if cliente_data.cpf:
            # Verifica duplicidade de CPF em Cliente
            cliente_cpf_query = select(Cliente).where(Cliente.cpf == cliente_data.cpf)
            if session.exec(cliente_cpf_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado por outro usuário!"
                )

            # Verifica duplicidade de CPF em Admin
            admin_cpf_query = select(Admin).where(Admin.cpf == cliente_data.cpf)
            if session.exec(admin_cpf_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado por um administrador!"
                )

            cliente_to_update.cpf = cliente_data.cpf

        if cliente_data.data_nascimento:
            cliente_to_update.data_nascimento = cliente_data.data_nascimento
        if cliente_data.telefone:
            cliente_to_update.telefone = cliente_data.telefone
        if cliente_data.cep:
            cliente_to_update.cep = cliente_data.cep
        if cliente_data.complemento:
            cliente_to_update.complemento = cliente_data.complemento
        if cliente_data.password:
            cliente_to_update.password = hash_password(cliente_data.password)
            
        # Salvar as alterações no banco de dados
        session.add(cliente_to_update)
        session.commit()
        session.refresh(cliente_to_update)

        return {"message": "Usuário atualizado com sucesso!", "cliente": cliente_to_update}

# Cadastro de clientes
@router.post('/cadastrar', status_code=status.HTTP_201_CREATED)
async def cadastrar_clientes(cliente_data: SignUpClienteRequest, ref: int | None = None):
    with Session(get_engine()) as session:
        
        # Verifica se já existe um usuário com esse e-mail
        sttm = select(Cliente).where(Cliente.email == cliente_data.email)
        cliente = session.exec(sttm).first()
        
        if cliente:
            raise HTTPException(status_code=400, detail='Já existe um usuário com esse e-mail!')

        # Verifica se já existe um usuário com o código de confirmação de e-mail
        sttm = select(Cliente).where(Cliente.cod_confirmacao_email == cliente_data.email)
        cliente = session.exec(sttm).first()
        
        if cliente:
            raise HTTPException(status_code=400, detail='E-mail já cadastrado anteriormente. Tente recuperar o e-mail!')

        # Verifica duplicidade de e-mail em administradores
        admin_email_query = select(Admin).where(Admin.email == cliente_data.email)
        if session.exec(admin_email_query).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail já cadastrado por um administrador!"
            )
        
        # Verifica duplicidade de CPF em usuários
        sttm = select(Cliente).where(Cliente.cpf == cliente_data.cpf)
        cliente = session.exec(sttm).first()

        if cliente:
            raise HTTPException(status_code=400, detail='CPF inválido')

        # Verifica duplicidade de CPF em administradores
        admin_cpf_query = select(Admin).where(Admin.cpf == cliente_data.cpf)
        if session.exec(admin_cpf_query).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF já cadastrado por um administrador!"
            )

        # Verifica se as senhas coincidem
        if cliente_data.password != cliente_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Senhas não coincidem!'
            )

        # Hash da senha
        hash = hash_password(cliente_data.password)
        codigo = gerar_codigo_confirmacao()
        
        if ref is not None:
            # Verifica codigo de indicacao
            sttm = select(Cliente).where(Cliente.id == ref)
            cliente_referenciado = session.exec(sttm).first()
            if cliente_referenciado:
                link = ref
        else:
            link = 0

        # Criação do usuário
        cliente = Cliente(
            nome=cliente_data.nome,
            email=cliente_data.email, 
            cod_confirmacao_email=codigo,
            password=hash,
            cpf=cliente_data.cpf,
            data_nascimento=cliente_data.data_nascimento,
            complemento=cliente_data.complemento,
            telefone=cliente_data.telefone,
            cep=cliente_data.cep,
            pontos_fidelidade=0,
            clube_fidelidade=False,
            cod_indicacao=link,
            status=True
        )
        
        # Gera a URL de confirmação
        url = f"{URL}/emails/confirmado/?codigo={codigo}"
        corpo_de_confirmacao = template_confirmacao(cliente.nome, url)

        # Envia o e-mail de confirmação
        email = Email(
            nome_remetente="Buy Tech",
            remetente=EMAIL,
            senha=KEY_EMAIL,
            destinatario=cliente.email,
            assunto="Confirmar E-mail",
            corpo=corpo_de_confirmacao
        )

        envio = enviar_email(
            email.nome_remetente, 
            email.remetente, 
            email.senha, 
            email.destinatario, 
            email.assunto, 
            email.corpo, 
            importante=True,
            html=True
        )

        if envio:
            session.add(cliente)
            session.commit()
            session.refresh(cliente)
            
            return {"message": "Usuário cadastrado com sucesso! E-mail de confirmação enviado."}
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao enviar o e-mail de confirmação."
        )

# Login de clientes
@router.post('/logar')
def logar_clientes(signin_data: SignInClienteRequest):
  with Session(get_engine()) as session:
    # pegar usuário por email
    
    sttm = select(Cliente).where(Cliente.email == signin_data.email)
    cliente = session.exec(sttm).first()
    
    if not cliente: # não encontrou usuário
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Email invalido!')
    
    # encontrou, então verificar a senha
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    is_correct = pwd_context.verify(signin_data.password, cliente.password)

    if not is_correct:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Senha incorrenta!')
      
    if cliente.cod_confirmacao_email !="Confirmado":
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail='E-mail não confirmado')
    
    if cliente.status == False:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Conta de cliente desativada!') 
    
    
    # Tá tudo OK pode gerar um Token JWT e devolver
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRES)
    access_token = jwt.encode({'sub': cliente.email, 'exp': expires_at}, key=SECRET_KEY, algorithm=ALGORITHM)

    expires_rt = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_EXPIRES)
    refresh_token = jwt.encode({'sub': cliente.email, 'exp': expires_rt}, key=SECRET_KEY, algorithm=ALGORITHM)
    
    return {'access_token': access_token, 'refresh_token': refresh_token}

# Autentica clientes
@router.get('/autenticar', response_model=Cliente)
def autenticar_clientes(cliente: Annotated[Cliente, Depends(get_logged_cliente)]):
  return cliente

# Atualiza clientes por id
@router.patch("/atualizar/{cliente_id}")
def atualizar_clientes_por_id(
    cliente_id: int,
    cliente_data: UpdateClienteRequest,
    cliente: Annotated[Cliente, Depends(get_logged_cliente)]
):
    if cliente.id != cliente_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        sttm = select(Cliente).where(Cliente.id == cliente_id)
        cliente_to_update = session.exec(sttm).first()

        if not cliente_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )
        
        if cliente_to_update.cod_confirmacao_email != "Confirmado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="E-mail não confirmado!"
            )

        # Atualizar os campos fornecidos
        if cliente_data.nome:
            cliente_to_update.nome = cliente_data.nome
            
        if cliente_data.email:
            # Verifica duplicidade de e-mail em Cliente
            cliente_email_query = select(Cliente).where(Cliente.email == cliente_data.email)
            if session.exec(cliente_email_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="E-mail já cadastrado por outro usuário!"
                )
            
            # Verifica duplicidade de e-mail em Admin
            admin_email_query = select(Admin).where(Admin.email == cliente_data.email)
            if session.exec(admin_email_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="E-mail já cadastrado por um administrador!"
                )

            # Atualizar o e-mail (mantendo o atual como "não confirmado")
            cliente_to_update.cod_confirmacao_email = cliente_to_update.email
            cliente_to_update.email = cliente_data.email

        if cliente_data.cpf:
            # Verifica duplicidade de CPF em Cliente
            cliente_cpf_query = select(Cliente).where(Cliente.cpf == cliente_data.cpf)
            if session.exec(cliente_cpf_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado por outro usuário!"
                )

            # Verifica duplicidade de CPF em Admin
            admin_cpf_query = select(Admin).where(Admin.cpf == cliente_data.cpf)
            if session.exec(admin_cpf_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado por um administrador!"
                )

            cliente_to_update.cpf = cliente_data.cpf

        if cliente_data.data_nascimento:
            cliente_to_update.data_nascimento = cliente_data.data_nascimento
        if cliente_data.telefone:
            cliente_to_update.telefone = cliente_data.telefone
        if cliente_data.cep:
            cliente_to_update.cep = cliente_data.cep
        if cliente_data.complemento:
            cliente_to_update.complemento = cliente_data.complemento
        if cliente_data.password:
            cliente_to_update.password = hash_password(cliente_data.password)
            
        # Salvar as alterações no banco de dados
        session.add(cliente_to_update)
        session.commit()
        session.refresh(cliente_to_update)

        return {"message": "Usuário atualizado com sucesso!", "cliente": cliente_to_update}

# Atualiza o status do usuarios para desativado
@router.patch("/desativar/{cliente_id}")
def desativar_clientes(cliente_id: int, cliente: Annotated[Cliente, Depends(get_logged_cliente)]
):
    if cliente.id != cliente_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        sttm = select(Cliente).where(Cliente.id == cliente_id)
        cliente_to_update = session.exec(sttm).first()

        if not cliente_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )

        cliente_to_update.status = False
        session.add(cliente_to_update)
        session.commit()
        session.refresh(cliente_to_update)

        return {"message": "Usuário desativado com sucesso!"}
 
# Adiministradores atualiza o status do usuarios para desativado      
@router.patch("/admin/desativar/{cliente_id}")
def desativar_ususarios_admin(cliente_id: int, admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem desativar usuários."
        )

    with Session(get_engine()) as session:
        sttm = select(Cliente).where(Cliente.id == cliente_id)
        cliente_to_update = session.exec(sttm).first()

        if not cliente_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )

        cliente_to_update.status = False
        session.add(cliente_to_update)
        session.commit()
        session.refresh(cliente_to_update)

        return {"message": "Usuário desativado com sucesso!"}
