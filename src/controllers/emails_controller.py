from fastapi import APIRouter, status, HTTPException
from decouple import config
from davidsousa import enviar_email
from src.models.emails_models import Email
from sqlmodel import Session, select
from src.database import get_engine
from src.models.clientes_models import Cliente
from src.models.admins_models import Admin
from src.html.email_redefinir_senha import template_redefinir_senha

from src.auth_utils import hash_password

EMAIL = config('EMAIL')
KEY_EMAIL = config('KEY_EMAIL')
URL= config('URL')

router = APIRouter()

import string
import random

# Gera codigo com 6 caracteres para confirmação
def gerar_codigo_confirmacao(tamanho=6):
        """Gera um código aleatório de confirmação."""
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choices(caracteres, k=tamanho))

# Lista os verbos disponiveis para esse controller
@router.options("", status_code=status.HTTP_200_OK)
async def options_emails():
    return { "methods": ["GET"] }

# Verifica se o email foi confirmado    
@router.get('/confirmado', status_code=status.HTTP_200_OK)
def email_confirmado(codigo: str):
    with Session(get_engine()) as session:
        clientes = select(Cliente).where(Cliente.cod_confirmacao_email == codigo)
        admins = select(Admin).where(Admin.cod_confirmacao_email == codigo)
        cliente_to_update = session.exec(clientes).first()
        admin_to_update = session.exec(admins).first()

        if not cliente_to_update and not admin_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Codigo de recuperação invalido!"
            )
        if cliente_to_update:

            if cliente_to_update.cod_confirmacao_email=="Confirmado":
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="E-mail já confirmado."
                )  
            if len(cliente_to_update.cod_confirmacao_email)>6:
                cliente_to_update.email=codigo
                
            cliente_to_update.cod_confirmacao_email = "Confirmado"
            session.add(cliente_to_update)
            session.commit()
            session.refresh(cliente_to_update)    
            
        if admin_to_update:
            if admin_to_update.cod_confirmacao_email=="Confirmado":
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="E-mail já confirmado."
                )  
            if len(admin_to_update.cod_confirmacao_email)>6:
                admin_to_update.email=codigo
                
            admin_to_update.cod_confirmacao_email = "Confirmado"
            session.add(admin_to_update)
            session.commit()
            session.refresh(admin_to_update)
            
        return {"email": True}
    
# Recuperar email
@router.get('/recuperar_email', status_code=status.HTTP_200_OK)
def recuperar_email(email: str | None = None, cpf: int | None = None):
    with Session(get_engine()) as session:
        cliente_to_update = None
        admin_to_update = None

        if email:
            # Verificar em Cliente
            sttm_cliente = select(Cliente).where(Cliente.cod_confirmacao_email == email)
            cliente_to_update = session.exec(sttm_cliente).first()
            if cliente_to_update and len(cliente_to_update.cod_confirmacao_email) > 6:
                cliente_to_update.email = cliente_to_update.cod_confirmacao_email
            
            # Verificar em Admin
            sttm_admin = select(Admin).where(Admin.cod_confirmacao_email == email)
            admin_to_update = session.exec(sttm_admin).first()
            if admin_to_update and len(admin_to_update.cod_confirmacao_email) > 6:
                admin_to_update.email = admin_to_update.cod_confirmacao_email
            
            # Caso nenhum dos dois tenha correspondência
            if not cliente_to_update and not admin_to_update:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="E-mail não está em recuperação!"
                )

        if cpf:
            # Verificar em Cliente
            sttm_cliente = select(Cliente).where(Cliente.cpf == cpf)
            cliente_to_update = session.exec(sttm_cliente).first()
            if cliente_to_update and len(cliente_to_update.cod_confirmacao_email) > 6:
                cliente_to_update.email = cliente_to_update.cod_confirmacao_email
            
            # Verificar em Admin
            sttm_admin = select(Admin).where(Admin.cpf == cpf)
            admin_to_update = session.exec(sttm_admin).first()
            if admin_to_update and len(admin_to_update.cod_confirmacao_email) > 6:
                admin_to_update.email = admin_to_update.cod_confirmacao_email
            
            # Caso nenhum dos dois tenha correspondência
            if not cliente_to_update and not admin_to_update:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="CPF inválido!"
                )

        # Atualizar e salvar no banco de dados
        if cliente_to_update:
            cliente_to_update.cod_confirmacao_email = "Confirmado"
            session.add(cliente_to_update)
            session.commit()
            session.refresh(cliente_to_update)

        if admin_to_update:
            admin_to_update.cod_confirmacao_email = "Confirmado"
            session.add(admin_to_update)
            session.commit()
            session.refresh(admin_to_update)

        # Retornar o sucesso
        if cliente_to_update or admin_to_update:
            return {"email": True}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhum registro foi atualizado!"
            )
 
# Recuperar senha
@router.get('/recuperar_senha', status_code=status.HTTP_200_OK)
def recuperar_senha(email: str | None = None):
    with Session(get_engine()) as session:
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail é obrigatório!"
            )

        # Verificar se é um administrador
        sttm = select(Admin).where(Admin.email == email)
        admin_to_update = session.exec(sttm).first()

        if admin_to_update and admin_to_update.cod_confirmacao_email == "Confirmado":
            password = gerar_codigo_confirmacao()
            corpo_de_confirmacao = template_redefinir_senha(admin_to_update.nome, password)
            destinatario = admin_to_update.email
            entidade = admin_to_update
        else:
            # Verificar se é um usuário comum
            sttm = select(Cliente).where(Cliente.email == email)
            cliente_to_update = session.exec(sttm).first()

            if cliente_to_update and cliente_to_update.cod_confirmacao_email == "Confirmado":
                password = gerar_codigo_confirmacao()
                corpo_de_confirmacao = template_redefinir_senha(cliente_to_update.nome, password)
                destinatario = cliente_to_update.email
                entidade = cliente_to_update
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="E-mail inválido!"
                )

        # Configurar o e-mail
        email_data = Email(
            nome_remetente="Buy Tech",
            remetente=EMAIL,
            senha=KEY_EMAIL,
            destinatario=destinatario,
            assunto="Recuperar senha",
            corpo=corpo_de_confirmacao
        )

        # Enviar o e-mail
        envio = enviar_email(
            email_data.nome_remetente,
            email_data.remetente,
            email_data.senha,
            email_data.destinatario,
            email_data.assunto,
            email_data.corpo,
            importante=True,
            html=True
        )

        if envio:
            # Atualizar a senha no banco de dados
            entidade.password = hash_password(password)
            session.add(entidade)
            session.commit()
            session.refresh(entidade)
            return {"email": True}

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao enviar o e-mail"
        )
