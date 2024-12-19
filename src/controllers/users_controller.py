from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_user, hash_password, SECRET_KEY, ALGORITHM
from src.database import get_engine
from src.models.user_models import BaseUser, SignInUserRequest, SignUpUserRequest, User,  UpdateUserRequest
from passlib.context import CryptContext
import jwt

ACCESS_EXPIRES=10 
REFRESH_EXPIRES=60*24*3 

router = APIRouter()

@router.post('/cadastrar', response_model=BaseUser)
def cadastrar_usuario(user_data: SignUpUserRequest, ref: int | None = None):

  with Session(get_engine()) as session:
    # pegar usuário por email
    sttm = select(User).where(User.email == user_data.email)
    user = session.exec(sttm).first()
    
    if user:
      raise HTTPException(status_code=400, detail='Já existe um usuário com esse email')

  if user_data.password != user_data.confirm_password:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='Senhas não coincidem!')
  
  # Hash da senha
  hash = hash_password(user_data.password)
  link = 0
  if ref != None:
    link = ref
    
  user = User(
    name=user_data.name,
    email=user_data.email, 
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
  
  with Session(get_engine()) as session:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
  

@router.post('/logar')
def logar_usuario(signin_data: SignInUserRequest):
  with Session(get_engine()) as session:
    # pegar usuário por email
    
    sttm = select(User).where(User.email == signin_data.email)
    user = session.exec(sttm).first()
    
    if not user: # não encontrou usuário
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Usuário e/ou senha incorreto(S)')
    
    # encontrou, então verificar a senha
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    is_correct = pwd_context.verify(signin_data.password, user.password)

    if not is_correct:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Usuário e/ou senha incorrento(S)')
      
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
    user: Annotated[User, Depends(get_logged_user)],
):
    with Session(get_engine()) as session:
        sttm = select(User).where(User.id == user_id)
        user_to_update = session.exec(sttm).first()

        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )
        
        # Atualizar os campos fornecidos
        if user_data.name:
            user_to_update.name = user_data.name
        if user_data.email:
            user_to_update.email = user_data.email
        if user_data.cpf:
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

