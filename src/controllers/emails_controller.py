from fastapi import APIRouter, status, HTTPException
from decouple import config
from davidsousa import enviar_email
from src.models.emails_models import Email
from sqlmodel import Session, select
from src.database import get_engine
from src.models.users_models import User
from src.html.email_redefinir_senha import template_redefinir_senha

from src.auth_utils import hash_password

EMAIL = config('EMAIL')
KEY_EMAIL = config('KEY_EMAIL')
URL= config('URL')
router = APIRouter()

import string
import random
def gerar_codigo_confirmacao(tamanho=6):
        """Gera um código aleatório de confirmação."""
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choices(caracteres, k=tamanho))

"""
# Confirma e-mail com codigo de confirmacao
@router.get('/confirmar', status_code=status.HTTP_200_OK)
def email_de_confirmacao(code: str):
    if code=="Confirmado":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="E-mail já confirmado."
            ) 
    if len(code)>6:
       raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Codigo invalido."
            )
                
    with Session(get_engine()) as session:
        statement = select(User).where(User.cod_confirmacao_email == code)
        user = session.exec(statement).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Codigo invalido."
            )
            
    url=f"{URL}/email/confirmado/?code={code}"
    
    corpo_de_confirmacao = template_confirmacao(user.name, url)
    
    email = Email(
        nome_remetente = "Buy Tech",
        remetente = EMAIL,
        senha = KEY_EMAIL,
        destinatario = user.email,
        assunto = "Confirmar E-mail",
        corpo = corpo_de_confirmacao
        )

    envio = enviar_email(
            email.nome_remetente, 
            email.remetente, 
            email.senha, 
            email.destinatario, 
            email.assunto, 
            email.corpo, 
            importante = True,
            html = True)
    if envio:
        return {"email": True}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Erro ao enviar e-mail"
    )
"""    
# Verifica se o email foi confirmado    
@router.get('/confirmado', status_code=status.HTTP_200_OK)
def email_confirmado(code: str):
    with Session(get_engine()) as session:
        sttm = select(User).where(User.cod_confirmacao_email == code)
        user_to_update = session.exec(sttm).first()

        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Codigo de recuperação invalido!"
            )
        if user_to_update.cod_confirmacao_email=="Confirmado":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="E-mail já confirmado."
            )  
        if len(user_to_update.cod_confirmacao_email)>6:
            user_to_update.email=code
        
        # Atualizar  o e-mail
        user_to_update.cod_confirmacao_email = "Confirmado"

        # Salvar as alterações no banco de dados
        session.add(user_to_update)
        session.commit()
        session.refresh(user_to_update)

        return {"email": True}
    
# Recuperar email
@router.get('/recuperar_email', status_code=status.HTTP_200_OK)
def recuperar_email(email: str | None=None, cpf: int | None=None):
                
    with Session(get_engine()) as session:
        if email:
            sttm = select(User).where(User.cod_confirmacao_email == email)
            user_to_update = session.exec(sttm).first()

            if not user_to_update:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="E-mail não esta em recuperação"
                )
            if len(user_to_update.cod_confirmacao_email)>6:
                user_to_update.email=user_to_update.cod_confirmacao_email
        
        if cpf:
            sttm = select(User).where(User.cpf == cpf)
            user_to_update = session.exec(sttm).first()

            if not user_to_update:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="CPF invalido!"
                ) 
            if len(user_to_update.cod_confirmacao_email)>6:
                user_to_update.email=user_to_update.cod_confirmacao_email
        
        # Atualizar  o e-mail
        user_to_update.cod_confirmacao_email = "Confirmado"

        # Salvar as alterações no banco de dados
        session.add(user_to_update)
        session.commit()
        session.refresh(user_to_update)

        return {"email": True}

    
# Recuperar senha
@router.get('/recuperar_senha', status_code=status.HTTP_200_OK)
def recuperar_senha(email: str | None=None):
                
    with Session(get_engine()) as session:
        if email:
            sttm = select(User).where(User.email == email)
            user_to_update = session.exec(sttm).first()
            
            if not user_to_update:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="E-mail invalido!"
                )
            if user_to_update.cod_confirmacao_email=="Confirmado":
                password = gerar_codigo_confirmacao()
                corpo_de_confirmacao = template_redefinir_senha(user_to_update.name, password)
                
                
                email = Email(
                    nome_remetente = "Buy Tech",
                    remetente = EMAIL,
                    senha = KEY_EMAIL,
                    destinatario = user_to_update.email,
                    assunto = "Recuperar senha",
                    corpo = corpo_de_confirmacao
                    )

                envio = enviar_email(
                        email.nome_remetente, 
                        email.remetente, 
                        email.senha, 
                        email.destinatario, 
                        email.assunto, 
                        email.corpo, 
                        importante = True,
                        html = True)
                if envio:
                    if user_to_update.password:
                        user_to_update.password = hash_password(password)
                    # Salvar as alterações no banco de dados
                    session.add(user_to_update)
                    session.commit()
                    session.refresh(user_to_update)
                    return {"email": True}
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Erro ao enviar e-mail"
                )