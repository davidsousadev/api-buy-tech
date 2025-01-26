import string
import random
from datetime import datetime, timedelta, timezone
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_admin, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
from src.database import get_engine
from src.models.admins_models import SignInAdminRequest, SignUpAdminRequest, Admin, AdminResponse, UpdateAdminRequest
from src.models.clientes_models import Cliente
from passlib.context import CryptContext
import jwt

from davidsousa import enviar_email
from src.models.emails_models import Email
from src.html.email_confirmacao import template_confirmacao
from decouple import config
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
async def options_admins():
    return { "methods": ["GET", "POST", "PATCH"] }

# Lista os administradores
@router.get("", response_model=list[AdminResponse])
def listar_admins(admin: Annotated[Admin, Depends(get_logged_admin)]):
    
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem listar admins."
        )

    with Session(get_engine()) as session:
        statement = select(Admin)
        admins = session.exec(statement).all()
        return [AdminResponse.model_validate(u) for u in admins]

# Cadastra administradores               
@router.post('/cadastrar')
def cadastrar_admins(admin_data: SignUpAdminRequest, ref: int | None = None):
    with Session(get_engine()) as session:
        
        # Pegar usuário e admin por email
        admins = select(Admin).where(Admin.email == admin_data.email)
        clientes = select(Cliente).where(Cliente.email == admin_data.email)
        admin = session.exec(admins).first()
        cliente = session.exec(clientes).first()
        if admin:
            raise HTTPException(status_code=400, detail='Já existe um administrador com esse email')
        if cliente:
            raise HTTPException(status_code=400, detail='Já existe um usuario com esse email')
        
        # Pegar usuário e admin por cpf
        admins = select(Admin).where(Admin.cpf == admin_data.cpf)
        clientes = select(Cliente).where(Cliente.cpf == admin_data.cpf)
        admin = session.exec(admins).first()
        cliente = session.exec(clientes).first()

        if admin:
          raise HTTPException(status_code=400, detail='CPF já cadastrado por outro admin!')
        if cliente:
          raise HTTPException(status_code=400, detail='CPF já cadastrado por um usuario!')
      
        if admin_data.password != admin_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Senhas não coincidem!'
            )

        # Hash da senha
        hash = hash_password(admin_data.password)
        link = 0
        if ref != None:
          link = ref

        codigo = gerar_codigo_confirmacao()
        
        admin = Admin(
                nome=admin_data.nome,
                email=admin_data.email, 
                cod_confirmacao_email=codigo,
                password=hash,
                cpf=admin_data.cpf,
                data_nascimento=admin_data.data_nascimento,
                complemento=admin_data.complemento,
                telefone=admin_data.telefone,
                cep=admin_data.cep,
                pontos_fidelidade=0,
                clube_fidelidade=False,
                cod_indicacao=link,
                status=True,
                admin=True
                )
        # Gera a URL de confirmação
        url = f"{URL}/emails/confirmado/?codigo={codigo}"
        corpo_de_confirmacao = template_confirmacao(admin.nome, url)

        # Envia o e-mail de confirmação
        email = Email(
            nome_remetente="Buy Tech",
            remetente=EMAIL,
            senha=KEY_EMAIL,
            destinatario=admin.email,
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
            session.add(admin)
            session.commit()
            session.refresh(admin)
            return {"message": "Administrador cadastrado com sucesso! E-mail de confirmação enviado."}

        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao enviar o e-mail de confirmação."
            )

# Logar administradores        
@router.post('/logar')
def logar_admins(signin_data: SignInAdminRequest):
  with Session(get_engine()) as session:
    # pegar usuário por email
    
    sttm = select(Admin).where(Admin.email == signin_data.email)
    admin = session.exec(sttm).first()
    
    if not admin: # Não encontrou Administrador
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Email incorreto!')
    
    if admin.cod_confirmacao_email !="Confirmado":
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail='E-mail não confirmado!')
    
    if admin.status == False:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Conta de administrador desativada!') 
    
    # encontrou, então verificar a senha
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    is_correct = pwd_context.verify(signin_data.password, admin.password)

    if not is_correct:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Usuário e/ou senha incorrento(S)')
    
    # Tá tudo OK pode gerar um Token JWT e devolver
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRES)
    access_token = jwt.encode({'sub': admin.email, 'exp': expires_at}, key=SECRET_KEY, algorithm=ALGORITHM)

    expires_rt = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_EXPIRES)
    refresh_token = jwt.encode({'sub': admin.email, 'exp': expires_rt}, key=SECRET_KEY, algorithm=ALGORITHM)


    return {'access_token': access_token, 'refresh_token': refresh_token}

# Autentica administradores
@router.get('/autenticar', response_model=Admin)
def autenticar_admins(admin: Annotated[Admin, Depends(get_logged_admin)]):
  return admin

# Atualiza alguns dados dos administradores por id
@router.patch("/atualizar/{admin_id}")
def atualizar_administrador(
    admin_id: int,
    admin_data: UpdateAdminRequest,
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem atualizar admins."
        )
    
    with Session(get_engine()) as session:
        # Buscar o administrador a ser atualizado
        sttm = select(Admin).where(Admin.id == admin_id)
        admin_to_update = session.exec(sttm).first()

        if not admin_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Administrador não encontrado."
            )
        
        if admin_to_update.cod_confirmacao_email != "Confirmado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail não confirmado!"
            )
        
        # Atualizar os campos fornecidos
        if admin_data.nome:
            admin_to_update.nome = admin_data.nome

        if admin_data.email:
            # Verificar duplicidade de e-mail em Admin
            admin_email = select(Admin).where(Admin.email == admin_data.email)
            if session.exec(admin_email).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="E-mail já cadastrado por outro administrador!"
                )

            # Verificar duplicidade de e-mail em Cliente
            cliente_email = select(Cliente).where(Cliente.email == admin_data.email)
            if session.exec(cliente_email).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="E-mail já cadastrado por um usuário!"
                )

            # Atualizar o e-mail (mantendo o atual como "não confirmado")
            admin_to_update.cod_confirmacao_email = admin_to_update.email
            admin_to_update.email = admin_data.email

        if admin_data.cpf:
            # Verificar duplicidade de CPF em Admin
            admin_cpf = select(Admin).where(Admin.cpf == admin_data.cpf)
            if session.exec(admin_cpf).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado por outro administrador!"
                )

            # Verificar duplicidade de CPF em Cliente
            cliente_cpf = select(Cliente).where(Cliente.cpf == admin_data.cpf)
            if session.exec(cliente_cpf).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado por um usuário!"
                )

            admin_to_update.cpf = admin_data.cpf

        if admin_data.data_nascimento:
            admin_to_update.data_nascimento = admin_data.data_nascimento
        if admin_data.telefone:
            admin_to_update.telefone = admin_data.telefone
        if admin_data.cep:
            admin_to_update.cep = admin_data.cep
        if admin_data.complemento:
            admin_to_update.complemento = admin_data.complemento 
        if admin_data.password:
            admin_to_update.password = hash_password(admin_data.password)

        # Salvar as alterações no banco de dados
        session.add(admin_to_update)
        session.commit()
        session.refresh(admin_to_update)

        return {"message": "Administrador atualizado com sucesso!", "Administrador": admin_to_update}

# Atualiza o status dos administradores por id
@router.patch("/desativar/{admin_id}")
def desativar_admins(admin_id: int, admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem desativar administradores."
        )

    with Session(get_engine()) as session:
        sttm = select(Admin).where(Admin.id == admin_id)
        admin_to_update = session.exec(sttm).first()

        if not admin_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Administrador não encontrado."
            )

        admin_to_update.status = False
        session.add(admin_to_update)
        session.commit()
        session.refresh(admin_to_update)

        return {"message": "Administrador desativado com sucesso!"}
