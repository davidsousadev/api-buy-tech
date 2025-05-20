import jwt
import string
import random

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from davidsousa import enviar_email
from typing import Annotated
from sqlmodel import Session, select
from sqlalchemy import or_
from sqlalchemy.sql import union_all

from src.database import get_engine
from src.auth_utils import get_logged_admin, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES

from src.models.admins_models import SignInAdminRequest, SignUpAdminRequest, Admin, AdminResponse, UpdateAdminRequest
from src.models.clientes_models import Cliente
from src.models.revendedores_models import Revendedor
from src.models.emails_models import Email

from src.html.email_confirmacao import template_confirmacao

from decouple import config

EMAIL = config('EMAIL')
KEY_EMAIL = config('KEY_EMAIL')
URL = config('URL')
URL_FRONT = config('URL_FRONT')

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
            status_code=status.HTTP_204_NO_CONTENT,
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

        # Verifica se já existe um admin, revendedor ou cliente com o código de confirmação de e-mail
        sttm = union_all(
            select(Admin.cod_confirmacao_email).where(Admin.cod_confirmacao_email == admin_data.email),
            select(Revendedor.cod_confirmacao_email).where(Revendedor.cod_confirmacao_email == admin_data.email),
            select(Cliente.cod_confirmacao_email).where(Cliente.cod_confirmacao_email == admin_data.email),
        )
        registro_existente = session.exec(sttm).first()

        if registro_existente:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail='E-mail já cadastrado anteriormente. Tente recuperar o e-mail!'
            )

        # Verifica se já existe um admin, revendedor ou cliente com o mesmo e-mail
        sttm = union_all(
            select(Admin.email).where(Admin.email == admin_data.email),
            select(Revendedor.email).where(Revendedor.email == admin_data.email),
            select(Cliente.email).where(Cliente.email == admin_data.email),
        )
        email_existente = session.exec(sttm).first()

        if email_existente:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail='E-mail já cadastrado anteriormente!'
            )

        # Verifica se já existe um admin ou cliente com o mesmo CPF
        sttm = union_all(
            select(Admin.cpf).where(Admin.cpf == admin_data.cpf),
            select(Cliente.cpf).where(Cliente.cpf == admin_data.cpf),
        )
        cpf_existente = session.exec(sttm).first()

        if cpf_existente:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail='CPF já cadastrado anteriormente!'
            )      
        if admin_data.password != admin_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail='Senhas não coincidem!'
            )

        # Hash da senha
        hash = hash_password(admin_data.password)

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
                status=True,
                admin=True
                )
        # Gera a URL de confirmação
        url = f"{URL_FRONT}/emails/confirmado/index.html?codigo={codigo}"
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
      raise HTTPException(status_code=status.HTTP_200_OK, 
        detail='Email incorreto!')
    
    if admin.cod_confirmacao_email !="Confirmado":
      raise HTTPException(
        status_code=status.HTTP_200_OK, 
        detail='E-mail não confirmado!')
    
    if admin.status == False:
      raise HTTPException(
        status_code=status.HTTP_200_OK, 
        detail='Conta de administrador desativada!') 
    
    # encontrou, então verificar a senha
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    is_correct = pwd_context.verify(signin_data.password, admin.password)

    if not is_correct:
      raise HTTPException(
        status_code=status.HTTP_200_OK, 
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

# Atualiza alguns dados dos administradores
@router.patch("/atualizar")
def atualizar_adminis(
    admin_data: UpdateAdminRequest,
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )
    
    with Session(get_engine()) as session:
        # Buscar o administrador a ser atualizado
        sttm = select(Admin).where(Admin.id == admin.id)
        admin_to_update = session.exec(sttm).first()

        if not admin_to_update:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Administrador não encontrado."
            )
        
        if admin_to_update.cod_confirmacao_email != "Confirmado":
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="E-mail não confirmado!"
            )
        
        # Atualizar os campos fornecidos
        if admin_data.nome and admin_to_update.nome != admin_data.nome:
            admin_to_update.nome = admin_data.nome
        if admin_data.email and admin_to_update.email != admin_data.email:
                # Verifica se já existe um admin, revendedor ou cliente com o código de confirmação de e-mail
            sttm = select(Admin, Revendedor, Cliente).where(
                or_(
                    Admin.cod_confirmacao_email == admin_data.email,
                    Revendedor.cod_confirmacao_email == admin_data.email,
                    Cliente.cod_confirmacao_email == admin_data.email
                )
            )
            registro_existente = session.exec(sttm).first()
    
            if registro_existente:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail='E-mail já cadastrado anteriormente. Tente recuperar o e-mail!'
                )
    
            # Verifica se já existe um admin, revendedor ou cliente com o mesmo e-mail
            sttm = select(Admin, Revendedor, Cliente).where(
                or_(
                    Admin.email == admin_data.email,
                    Revendedor.email == admin_data.email,
                    Cliente.email == admin_data.email
                )
            )
            email_existente = session.exec(sttm).first()
    
            if email_existente:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail='E-mail já cadastrado anteriormente!'
                )

            # Atualizar o e-mail (mantendo o atual como "não confirmado")
            admin_to_update.cod_confirmacao_email = admin_to_update.email
            admin_to_update.email = admin_data.email
        if admin_data.cpf and admin_to_update.cpf != admin_data.cpf:
            
            # Verifica se já existe um admin ou cliente com o mesmo CPF
            sttm = select(Admin, Cliente).where(
                or_(
                    Admin.cpf == admin_data.cpf,
                    Cliente.cpf == admin_data.cpf
                )
            )
            cpf_existente = session.exec(sttm).first()

            if cpf_existente:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail='CPF já cadastrado anteriormente!'
                )

            admin_to_update.cpf = admin_data.cpf
        if admin_data.data_nascimento and admin_to_update.data_nascimento != admin_data.data_nascimento:
            admin_to_update.data_nascimento = admin_data.data_nascimento
        if admin_data.telefone and admin_to_update.telefone != admin_data.telefone:
            admin_to_update.telefone = admin_data.telefone
        if admin_data.cep and admin_to_update.cep != admin_data.cep:
            admin_to_update.cep = admin_data.cep
        if admin_data.complemento and admin_to_update.complemento != admin_data.complemento:
            admin_to_update.complemento = admin_data.complemento 
        if admin_data.password and admin_to_update.password != hash_password(admin_data.password):
            admin_to_update.password = hash_password(admin_data.password)

        # Salvar as alterações no banco de dados
        session.add(admin_to_update)
        session.commit()
        session.refresh(admin_to_update)

        return {"message": "Administrador atualizado com sucesso!", "Administrador": admin_to_update}

# Atualiza alguns dados dos administradores por id
@router.patch("/atualizar/{admin_id}")
def atualizar_adminis_por_id(
    admin_id: int,
    admin_data: UpdateAdminRequest,
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado! Apenas administradores podem atualizar admins."
        )
    
    with Session(get_engine()) as session:
        # Buscar o administrador a ser atualizado
        sttm = select(Admin).where(Admin.id == admin_id)
        admin_to_update = session.exec(sttm).first()

        if not admin_to_update:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Administrador não encontrado."
            )
        
        if admin_to_update.cod_confirmacao_email != "Confirmado":
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="E-mail não confirmado!"
            )
        
        # Atualizar os campos fornecidos
        if admin_data.nome and admin_to_update.nome != admin_data.nome:
            admin_to_update.nome = admin_data.nome
        if admin_data.email and admin_to_update.email != admin_data.email:
                # Verifica se já existe um admin, revendedor ou cliente com o código de confirmação de e-mail
            sttm = select(Admin, Revendedor, Cliente).where(
                or_(
                    Admin.cod_confirmacao_email == admin_data.email,
                    Revendedor.cod_confirmacao_email == admin_data.email,
                    Cliente.cod_confirmacao_email == admin_data.email
                )
            )
            registro_existente = session.exec(sttm).first()
    
            if registro_existente:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail='E-mail já cadastrado anteriormente. Tente recuperar o e-mail!'
                )
    
            # Verifica se já existe um admin, revendedor ou cliente com o mesmo e-mail
            sttm = select(Admin, Revendedor, Cliente).where(
                or_(
                    Admin.email == admin_data.email,
                    Revendedor.email == admin_data.email,
                    Cliente.email == admin_data.email
                )
            )
            email_existente = session.exec(sttm).first()
    
            if email_existente:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail='E-mail já cadastrado anteriormente!'
                )

            # Atualizar o e-mail (mantendo o atual como "não confirmado")
            admin_to_update.cod_confirmacao_email = admin_to_update.email
            admin_to_update.email = admin_data.email
        if admin_data.cpf and admin_to_update.cpf != admin_data.cpf:
            
            # Verifica se já existe um admin ou cliente com o mesmo CPF
            sttm = select(Admin, Cliente).where(
                or_(
                    Admin.cpf == admin_data.cpf,
                    Cliente.cpf == admin_data.cpf
                )
            )
            cpf_existente = session.exec(sttm).first()

            if cpf_existente:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail='CPF já cadastrado anteriormente!'
                )

            admin_to_update.cpf = admin_data.cpf
        if admin_data.data_nascimento and admin_to_update.data_nascimento != admin_data.data_nascimento:
            admin_to_update.data_nascimento = admin_data.data_nascimento
        if admin_data.telefone and admin_to_update.telefone != admin_data.telefone:
            admin_to_update.telefone = admin_data.telefone
        if admin_data.cep and admin_to_update.cep != admin_data.cep:
            admin_to_update.cep = admin_data.cep
        if admin_data.complemento and admin_to_update.complemento != admin_data.complemento:
            admin_to_update.complemento = admin_data.complemento 
        if admin_data.password and admin_to_update.password != hash_password(admin_data.password):
            admin_to_update.password = hash_password(admin_data.password)

        # Salvar as alterações no banco de dados
        session.add(admin_to_update)
        session.commit()
        session.refresh(admin_to_update)

        return {"message": "Administrador atualizado com sucesso!", "Administrador": admin_to_update}

# Atualiza o status dos administradores por id para desativado ou ativado
@router.patch("/atualizar_status/{admin_id}")
def atualizar_status_admins_por_id(admin_id: int, admin: Annotated[Admin, Depends(get_logged_admin)]):
    
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado! Apenas administradores podem desativar administradores."
        )

    with Session(get_engine()) as session:
        sttm = select(Admin).where(Admin.id == admin_id)
        admin_to_update = session.exec(sttm).first()

        if not admin_to_update:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Administrador não encontrado."
            )

        if admin_to_update.status == False:
            admin_to_update.status = True
        elif admin_to_update.status == True:
           admin_to_update.status = False
           
        session.add(admin_to_update)
        session.commit()
        session.refresh(admin_to_update)

        return {"message": "Administrador desativado com sucesso!"}
