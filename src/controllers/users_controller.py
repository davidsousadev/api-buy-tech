import string
import random
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_user, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
from src.database import get_engine
from src.models.users_models import BaseUser, SignInUserRequest, SignUpUserRequest, User,  UpdateUserRequest
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

@router.post('/cadastrar', status_code=status.HTTP_201_CREATED)
async def cadastrar_usuario(user_data: SignUpUserRequest, ref: int | None = None):

  with Session(get_engine()) as session:
    
    # Pegar usuário por email
    sttm = select(User).where(User.email == user_data.email)
    user = session.exec(sttm).first()
    
    if user:
      raise HTTPException(status_code=400, detail='Já existe um usuário com esse email!')
    
    # Pegar usuário por codigo de confirmação de email já cadastrado anteriormente e confirmado
    sttm = select(User).where(User.cod_confirmacao_email == user_data.email)
    user = session.exec(sttm).first()
  
    if user:
      raise HTTPException(status_code=400, detail='E-mail já cadastrado anteriormente tente recuperar o email!')
    
    # Pegar usuário por cpf
    sttm = select(User).where(User.cpf == user_data.cpf)
    user = session.exec(sttm).first()
    
    if user:
      raise HTTPException(status_code=400, detail='CPF invalido')

    if user_data.password != user_data.confirm_password:
      raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='Senhas não coincidem!')
  
    # Hash da senha
    hash = hash_password(user_data.password)
    link = 0

    if ref != None:
      link = ref

    code = gerar_codigo_confirmacao() 

    user = User(
      name=user_data.name,
      email=user_data.email, 
      cod_confirmacao_email=code,
      password=hash,
      cpf=user_data.cpf,
      data_nascimento=user_data.data_nascimento,
      telefone=user_data.telefone,
      cep=user_data.cep,
      pontos_fidelidade=0,
      clube_fidelidade=False,
      cod_indicacao=link,
      status=True
      )

    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Gera a URL de confirmação
    url = f"{URL}/email/confirmado/?code={code}"
    corpo_de_confirmacao = template_confirmacao(user.name, url)

    # Envia o e-mail de confirmação
    email = Email(
        nome_remetente="Buy Tech",
        remetente=EMAIL,
        senha=KEY_EMAIL,
        destinatario=user.email,
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
        return {"message": "Usuário cadastrado com sucesso! E-mail de confirmação enviado."}
    
    raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao enviar o e-mail de confirmação."
        )

@router.post('/logar')
def logar_usuario(signin_data: SignInUserRequest):
  with Session(get_engine()) as session:
    # pegar usuário por email
    
    sttm = select(User).where(User.email == signin_data.email)
    user = session.exec(sttm).first()
    
    if not user: # não encontrou usuário
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Email invalido!')
    
    # encontrou, então verificar a senha
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    is_correct = pwd_context.verify(signin_data.password, user.password)

    if not is_correct:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Senha incorrenta!')
      
    if user.cod_confirmacao_email !="Confirmado":
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail='E-mail não confirmado')
      
    # Tá tudo OK pode gerar um Token JWT e devolver
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRES)
    access_token = jwt.encode({'sub': user.email, 'exp': expires_at}, key=SECRET_KEY, algorithm=ALGORITHM)

    expires_rt = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_EXPIRES)
    refresh_token = jwt.encode({'sub': user.email, 'exp': expires_rt}, key=SECRET_KEY, algorithm=ALGORITHM)
    
    return {'access_token': access_token, 'refresh_token': refresh_token}

@router.get('/autenticar', response_model=User)
def autenticar_usuario(user: Annotated[User, Depends(get_logged_user)]):
  return user

@router.patch("/atualizar/{user_id}")
def atualizar_usuario_por_id(
    user_id: int,
    user_data: UpdateUserRequest,
    user: Annotated[User, Depends(get_logged_user)]
):
    if user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
    with Session(get_engine()) as session:
        sttm = select(User).where(User.id == user_id)
        user_to_update = session.exec(sttm).first()

        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )
        if user_to_update.cod_confirmacao_email != "Confirmado":
          raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, 
                        detail='E-mail não confirmado!')

        # Atualizar os campos fornecidos
        if user_data.name:
            user_to_update.name = user_data.name
            
        if user_data.email:
          # Verifica se ja existe um email já cadastrado igual
          sttm = select(User).where(User.email == user_data.email)
          user = session.exec(sttm).first()
          
          if user:
            raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, 
                        detail='E-mail já cadastrado!')
            
          # Verifica se ja existe um email já cadastrado e confirmado anteriormente
          sttm = select(User).where(User.cod_confirmacao_email == user_data.email)
          user = session.exec(sttm).first()
          
          if user:
            raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, 
                        detail='E-mail já confirmado por outro usuario!')
          
          if not user:
            user_to_update.cod_confirmacao_email=user_to_update.email
            user_to_update.email = user_data.email
             
        if user_data.cpf:
          # Pegar usuário por cpf
          sttm = select(User).where(User.cpf == user_data.cpf)
          user = session.exec(sttm).first()

          if user:
            raise HTTPException(status_code=400, detail='CPF invalido')
          
          user_to_update.cpf = user_data.cpf
               
        if user_data.data_nascimento:
            user_to_update.data_nascimento = user_data.data_nascimento
        if user_data.telefone:
            user_to_update.telefone = user_data.telefone
        if user_data.cep:
            user_to_update.cep = user_data.cep
        if user_data.password:
            user_to_update.password = hash_password(user_data.password)
            
        # Salvar as alterações no banco de dados
        session.add(user_to_update)
        session.commit()
        session.refresh(user_to_update)

        return {"message": "Usuário atualizado com sucesso!", "user": user_to_update}


