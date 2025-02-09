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
from src.auth_utils import get_logged_revendedor, get_logged_admin, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES

from src.models.revendedores_models import SignInRevendedorRequest, SignUpRevendedorRequest, Revendedor, RevendedorResponse, UpdateRevendedorRequest
from src.models.admins_models import Admin
from src.models.clientes_models import Cliente
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
async def options_revendedores():
    return { "methods": ["GET", "POST", "PATCH"] }

# Endpoint para verificar duplicidade de CNPJ
@router.get("/verificar-cnpj")
async def verificar_cnpj(cnpj: int):
    with Session(get_engine()) as session:
        # Verifica duplicidade em revendedores
        statement = select(revendedor).where(Revendedor.cnpj == cnpj)
        revendedor = session.exec(statement).first()
        
        if revendedor:
            raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")

    return {"cnpj": True}

# Admins Listar Revendedores
@router.get("", response_model=list[RevendedorResponse])
def listar_revendedores(admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem listar revendedores."
        )

    with Session(get_engine()) as session:
        statement = select(Revendedor)
        revendedores = session.exec(statement).all()
        return [RevendedorResponse.model_validate(u) for u in revendedores]
  
# Cadastrar Revendedores        
@router.post('/cadastrar')
def cadastrar_revendedores(revendedor_data: SignUpRevendedorRequest):
    with Session(get_engine()) as session:
        
        # Verifica se já existe um admin, revendedor ou cliente com o código de confirmação de e-mail
        sttm = union_all(
            select(Admin.cod_confirmacao_email).where(Admin.cod_confirmacao_email == revendedor_data.email),
            select(Revendedor.cod_confirmacao_email).where(Revendedor.cod_confirmacao_email == revendedor_data.email),
            select(Cliente.cod_confirmacao_email).where(Cliente.cod_confirmacao_email == revendedor_data.email),
        )
        registro_existente = session.exec(sttm).first()

        if registro_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='E-mail já cadastrado anteriormente. Tente recuperar o e-mail!'
            )

        # Verifica se já existe um admin, revendedor ou cliente com o mesmo e-mail
        sttm = union_all(
            select(Admin.email).where(Admin.email == revendedor_data.email),
            select(Revendedor.email).where(Revendedor.email == revendedor_data.email),
            select(Cliente.email).where(Cliente.email == revendedor_data.email),
        )
        email_existente = session.exec(sttm).first()

        if email_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='E-mail já cadastrado anteriormente!'
            )
            
        # Verifica se já existe um revendedor com o mesmo CNPJ
        sttm = select(Revendedor).where(Revendedor.cnpj == revendedor_data.cnpj)
        cnpj_existente = session.exec(sttm).first()

        if cnpj_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='CNPJ já cadastrado anteriormente!'
            )

        if revendedor_data.password != revendedor_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Senhas não coincidem!'
            )

        # Hash da senha
        hash = hash_password(revendedor_data.password)
        
        codigo = gerar_codigo_confirmacao()
        
        revendedor = Revendedor(
                razao_social=revendedor_data.razao_social,
                email=revendedor_data.email, 
                cod_confirmacao_email=codigo,
                password=hash,
                cnpj=revendedor_data.cnpj,
                inscricao_estadual=revendedor_data.inscricao_estadual,
                telefone=revendedor_data.telefone,
                status=True,
                )
        # Gera a URL de confirmação
        url = f"{URL}/emails/confirmado/?codigo={codigo}"
        corpo_de_confirmacao = template_confirmacao(revendedor.razao_social, url)

        # Envia o e-mail de confirmação
        email = Email(
            nome_remetente="Buy Tech",
            remetente=EMAIL,
            senha=KEY_EMAIL,
            destinatario=revendedor.email,
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
            session.add(revendedor)
            session.commit()
            session.refresh(revendedor)
            return {"message": "Revendedor cadastrado com sucesso! E-mail de confirmação enviado."}

        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao enviar o e-mail de confirmação."
            )
  
# Logar revendedores      
@router.post('/logar')
def logar_revendedores(signin_data: SignInRevendedorRequest):
  with Session(get_engine()) as session:
    # pegar revendedor por email
    sttm = select(Revendedor).where(Revendedor.email == signin_data.email)
    revendedor = session.exec(sttm).first()
    
    if not revendedor: # Não encontrou Revendedor
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Email incorreto!')
    
    if revendedor.cod_confirmacao_email !="Confirmado":
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail='E-mail não confirmado!')
    
    if revendedor.status == False:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Conta de revendedor desativada!') 
    
    # encontrou, então verificar a senha
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    is_correct = pwd_context.verify(signin_data.password, revendedor.password)

    if not is_correct:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail='E-mail e/ou senha incorrento(S)')
    
    # Tá tudo OK pode gerar um Token JWT e devolver
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRES)
    access_token = jwt.encode({'sub': revendedor.email, 'exp': expires_at}, key=SECRET_KEY, algorithm=ALGORITHM)

    expires_rt = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_EXPIRES)
    refresh_token = jwt.encode({'sub': revendedor.email, 'exp': expires_rt}, key=SECRET_KEY, algorithm=ALGORITHM)


    return {'access_token': access_token, 'refresh_token': refresh_token}

# Autenticar revendedores
@router.get('/autenticar', response_model=Revendedor)
def autenticar_revendedores(revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)]):
  return revendedor

# Atualizar revendedores por id
@router.patch("/atualizar/{revendedor_id}")
def atualizar_revendedor( revendedor_id: int, revendedor_data: UpdateRevendedorRequest, revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)],
):
    if revendedor_id != revendedor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
    
    with Session(get_engine()) as session:
        # Buscar o revendedor a ser atualizado
        sttm = select(Revendedor).where(Revendedor.id == revendedor.id)
        revendedor_to_update = session.exec(sttm).first()

        if not revendedor_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Revendedor não encontrado."
            )
        
        if revendedor_to_update.cod_confirmacao_email != "Confirmado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail não confirmado!"
            )
        
        # Atualizar os campos fornecidos
        if revendedor_data.razao_social and revendedor_to_update.razao_social != revendedor_data.razao_social:
            revendedor_to_update.razao_social = revendedor_data.razao_social

        if revendedor_data.email and revendedor_to_update.email != revendedor_data.email:
            # Verifica se já existe um admin, revendedor ou cliente com o código de confirmação de e-mail
            sttm = select(Admin, Revendedor, Cliente).where(
                or_(
                    Admin.cod_confirmacao_email == revendedor_data.email,
                    Revendedor.cod_confirmacao_email == revendedor_data.email,
                    Cliente.cod_confirmacao_email == revendedor_data.email
                )
            )
            registro_existente = session.exec(sttm).first()

            if registro_existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='E-mail já cadastrado anteriormente. Tente recuperar o e-mail!'
                )

            # Verifica se já existe um admin, revendedor ou cliente com o mesmo e-mail
            sttm = select(Admin, Revendedor, Cliente).where(
                or_(
                    Admin.email == revendedor_data.email,
                    Revendedor.email == revendedor_data.email,
                    Cliente.email == revendedor_data.email
                )
            )
            email_existente = session.exec(sttm).first()

            if email_existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='E-mail já cadastrado anteriormente!'
                )

            # Atualizar o e-mail (mantendo o atual como "não confirmado")
            revendedor_to_update.cod_confirmacao_email = revendedor_to_update.email
            revendedor_to_update.email = revendedor_data.email

        if revendedor_data.cnpj and revendedor_to_update.cnpj != revendedor_data.cnpj:
            
            # Verificar duplicidade de CNPJ em Revendedor
            revendedor_cnpj = select(Revendedor).where(Revendedor.cnpj == revendedor_data.cnpj)
            if session.exec(revendedor_cnpj).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CNPJ já cadastrado por outro Revendedor!"
                )
            revendedor_to_update.cnpj = revendedor_data.cnpj

        if revendedor_data.inscricao_estadual and revendedor_to_update.inscricao_estadual != revendedor_data.inscricao_estadual:
            
            # Verificar duplicidade de CNPJ em Revendedor
            revendedor_inscricao_estadual = select(Revendedor).where(Revendedor.inscricao_estadual == revendedor_data.inscricao_estadual)
            revendedor_duplicicade = session.exec(revendedor_inscricao_estadual).first()
            
            if revendedor_duplicicade and revendedor_duplicicade.cnpj != revendedor_data.cnpj:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incrição Estadual já cadastrada por outro Revendedor!"
                )
            revendedor_to_update.inscricao_estadual = revendedor_data.inscricao_estadual
            
        if revendedor_data.telefone and revendedor_to_update.telefone != revendedor_data.telefone:
            revendedor_to_update.telefone = revendedor_data.telefone
 
        if revendedor_data.password and revendedor_to_update.password != hash_password(revendedor_data.password):
            revendedor_to_update.password = hash_password(revendedor_data.password)

        # Salvar as alterações no banco de dados
        session.add(revendedor_to_update)
        session.commit()
        session.refresh(revendedor_to_update)

        return {"message": "Revendedor atualizado com sucesso!", "Revendedor": revendedor_to_update}

# Desativar revendedores por id
@router.patch("/desativar/{revendedor_id}")
def desativar_revendedor(revendedor_id: int, revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)]):
    
    if revendedor_id != revendedor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        sttm = select(Revendedor).where(Revendedor.id == revendedor_id)
        revendedor_to_update = session.exec(sttm).first()

        if not revendedor_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Revendedor não encontrado."
            )

        revendedor_to_update.status = False
        session.add(revendedor_to_update)
        session.commit()
        session.refresh(revendedor_to_update)

        return {"message": "Revendedor desativado com sucesso!"}

# Adiministradores Atualiza status revendedores por id para desativado ou ativado
@router.patch("/admin/atualizar_status/{revendedor_id}")
def atualizar_status_admin_revendedor_por_id(revendedor_id: int, admin: Annotated[Admin, Depends(get_logged_admin)]):
    
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        sttm = select(Revendedor).where(Revendedor.id == revendedor_id)
        revendedor_to_update = session.exec(sttm).first()

        if not revendedor_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Revendedor não encontrado."
            )

        if revendedor_to_update.status == False:
            revendedor_to_update.status = True
        elif revendedor_to_update.status == True:
           revendedor_to_update.status = False
           
        session.add(revendedor_to_update)
        session.commit()
        session.refresh(revendedor_to_update)

        return {"message": "Revendedor desativado com sucesso!"}