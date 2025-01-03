import string
import random
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime, timedelta, timezone
from src.auth_utils import get_logged_cotista, get_logged_admin, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
from src.database import get_engine
from src.models.cotistas_models import SignInCotistaRequest, SignUpCotistaRequest, Cotista, UpdateCotistaRequest, CotistaResponse
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

def gerar_codigo_confirmacao(tamanho=6):
        """Gera um código aleatório de confirmação."""
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choices(caracteres, k=tamanho))

@router.get("", response_model=list[CotistaResponse])
def listar_usuarios(admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem listar usuarios."
        )

    with Session(get_engine()) as session:
        statement = select(Cotista)
        cotistas = session.exec(statement).all()
        return [CotistaResponse.model_validate(u) for u in cotistas]

@router.patch("/admin/atualizar/{cotista_id}")
def atualizar_usuarios_por_id(
    cotista_id: int,
    cotista_data: UpdateCotistaRequest,
    admin: Annotated[Cotista, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
    
    with Session(get_engine()) as session:
        sttm = select(Cotista).where(Cotista.id == cotista_id)
        cotista_to_update = session.exec(sttm).first()

        if not cotista_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )
        
        if cotista_to_update.cod_confirmacao_email != "Confirmado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="E-mail não confirmado!"
            )

        # Atualizar os campos fornecidos
        if cotista_data.nome:
            cotista_to_update.nome = cotista_data.nome
            
        if cotista_data.email:
            # Verifica duplicidade de e-mail em cotista
            cotista_email_query = select(Cotista).where(Cotista.email == cotista_data.email)
            if session.exec(cotista_email_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="E-mail já cadastrado por outro usuário!"
                )
            
            # Verifica duplicidade de e-mail em Admin
            admin_email_query = select(Admin).where(Admin.email == cotista_data.email)
            if session.exec(admin_email_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="E-mail já cadastrado por um administrador!"
                )

            # Atualizar o e-mail (mantendo o atual como "não confirmado")
            cotista_to_update.cod_confirmacao_email = cotista_to_update.email
            cotista_to_update.email = cotista_data.email

        if cotista_data.cpf:
            # Verifica duplicidade de CPF em cotista
            cotista_cpf_query = select(Cotista).where(Cotista.cpf == cotista_data.cpf)
            if session.exec(cotista_cpf_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado por outro usuário!"
                )

            # Verifica duplicidade de CPF em Admin
            admin_cpf_query = select(Admin).where(Admin.cpf == cotista_data.cpf)
            if session.exec(admin_cpf_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado por um administrador!"
                )

            cotista_to_update.cpf = cotista_data.cpf

        if cotista_data.data_nascimento:
            cotista_to_update.data_nascimento = cotista_data.data_nascimento
        if cotista_data.telefone:
            cotista_to_update.telefone = cotista_data.telefone
        if cotista_data.cep:
            cotista_to_update.cep = cotista_data.cep
        if cotista_data.password:
            cotista_to_update.password = hash_password(cotista_data.password)
            
        # Salvar as alterações no banco de dados
        session.add(cotista_to_update)
        session.commit()
        session.refresh(cotista_to_update)

        return {"message": "Usuário atualizado com sucesso!", "cotista": cotista_to_update}

@router.patch("/atualizar/{cotista_id}")
def atualizar_usuario_por_id(
    cotista_id: int,
    cotista_data: UpdateCotistaRequest,
    cotista: Annotated[Cotista, Depends(get_logged_cotista)]
):
    if cotista.id != cotista_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        sttm = select(cotista).where(cotista.id == cotista_id)
        cotista_to_update = session.exec(sttm).first()

        if not cotista_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )
        
        if cotista_to_update.cod_confirmacao_email != "Confirmado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="E-mail não confirmado!"
            )

        # Atualizar os campos fornecidos
        if cotista_data.nome:
            cotista_to_update.nome = cotista_data.nome
            
        if cotista_data.email:
            # Verifica duplicidade de e-mail em cotista
            cotista_email_query = select(cotista).where(cotista.email == cotista_data.email)
            if session.exec(cotista_email_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="E-mail já cadastrado por outro usuário!"
                )
            
            # Verifica duplicidade de e-mail em Admin
            admin_email_query = select(Admin).where(Admin.email == cotista_data.email)
            if session.exec(admin_email_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="E-mail já cadastrado por um administrador!"
                )

            # Atualizar o e-mail (mantendo o atual como "não confirmado")
            cotista_to_update.cod_confirmacao_email = cotista_to_update.email
            cotista_to_update.email = cotista_data.email

        if cotista_data.cpf:
            # Verifica duplicidade de CPF em cotista
            cotista_cpf_query = select(cotista).where(cotista.cpf == cotista_data.cpf)
            if session.exec(cotista_cpf_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado por outro usuário!"
                )

            # Verifica duplicidade de CPF em Admin
            admin_cpf_query = select(Admin).where(Admin.cpf == cotista_data.cpf)
            if session.exec(admin_cpf_query).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado por um administrador!"
                )

            cotista_to_update.cpf = cotista_data.cpf

        if cotista_data.data_nascimento:
            cotista_to_update.data_nascimento = cotista_data.data_nascimento
        if cotista_data.telefone:
            cotista_to_update.telefone = cotista_data.telefone
        if cotista_data.cep:
            cotista_to_update.cep = cotista_data.cep
        if cotista_data.password:
            cotista_to_update.password = hash_password(cotista_data.password)
            
        # Salvar as alterações no banco de dados
        session.add(cotista_to_update)
        session.commit()
        session.refresh(cotista_to_update)

        return {"message": "Usuário atualizado com sucesso!", "cotista": cotista_to_update}

@router.patch("/desativar/{cotista_id}")
def desativar_ususarios(cotista_id: int, cotista: Annotated[Cotista, Depends(get_logged_cotista)]
):
    if cotista.id != cotista_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        sttm = select(cotista).where(cotista.id == cotista_id)
        cotista_to_update = session.exec(sttm).first()

        if not cotista_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )

        cotista_to_update.status = False
        session.add(cotista_to_update)
        session.commit()
        session.refresh(cotista_to_update)

        return {"message": "Usuário desativado com sucesso!"}
       
@router.patch("/usuarios/desativar/{cotista_id}")
def desativar_ususarios(cotista_id: int, admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem desativar usuários."
        )

    with Session(get_engine()) as session:
        sttm = select(Cotista).where(Cotista.id == cotista_id)
        cotista_to_update = session.exec(sttm).first()

        if not cotista_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )

        cotista_to_update.status = False
        session.add(cotista_to_update)
        session.commit()
        session.refresh(cotista_to_update)

        return {"message": "Usuário desativado com sucesso!"}
    
    