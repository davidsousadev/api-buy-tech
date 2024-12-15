from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from decouple import config
from src.auth_utils import get_logged_user, hash_password
from src.database import get_engine
from src.models import BaseUser, SignInUserRequest, SignUpUserRequest, User, UserData
from passlib.context import CryptContext
import jwt

router = APIRouter()

SECRET_KEY = config('SECRET_KEY')
ALGORITHM = config('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = 10
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 3


@router.post('/signup', response_model=BaseUser)
def signup(user_data: SignUpUserRequest, ref: str | None = None):

  with Session(get_engine()) as session:
    # pegar usuário por username
    sttm = select(User).where(User.username == user_data.username)
    user = session.exec(sttm).first()
    
    if user:
      raise HTTPException(status_code=400, detail='Já existe um usuário com esse username')


  if user_data.password != user_data.confirm_password:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='Senhas não coincidem!')
  
  # Hash da senha
  hash = hash_password(user_data.password)
  link = ""
  if ref != None:
    link = ref
    
  user = User(email=user_data.email, 
    name=user_data.name, 
    username=user_data.username,
    password=hash,
    pontos_fidelidade=0,
    clube_fidelidade=False,
    link_indicacao=link
    )
  
  with Session(get_engine()) as session:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
  

@router.post('/signin')
def signin(signin_data: SignInUserRequest):
  with Session(get_engine()) as session:
    # pegar usuário por username
    
    sttm = select(User).where(User.username == signin_data.username)
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
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode({'sub': user.username, 'exp': expires_at}, key=SECRET_KEY, algorithm=ALGORITHM)

    expires_rt = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = jwt.encode({'sub': user.username, 'exp': expires_rt}, key=SECRET_KEY, algorithm=ALGORITHM)


    return {'access_token': access_token, 'refresh_token': refresh_token}

@router.get('/me', response_model=UserData)
def me(user: Annotated[User, Depends(get_logged_user)]):
  return user