from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlmodel import Session, select
from decouple import config
from src.database import get_engine
from src.models.user_models import User
from src.models.admin_models import Admin

SECRET_KEY = config('SECRET_KEY')
ALGORITHM = config('ALGORITHM')
ACCESS_EXPIRES=10 
REFRESH_EXPIRES=60*24*3 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='signin')

async def get_logged_user(token: Annotated[str, Depends(oauth2_scheme)]):
    # Vai pegar o Token na Request, se válido
    # pegará o usuário no BD para confirmar e retornar ele
    exception = HTTPException(status_code=401, detail='Não autorizado!')
    invalid_exception = HTTPException(status_code=401, detail='Token inválido!')
    expired_exception = HTTPException(status_code=401, detail='Token expirado!')

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        email = payload.get('sub')

        if not email: 
            raise exception

        with Session(get_engine()) as session:
            sttm = select(User).where(User.email == email)
            user = session.exec(sttm).first()

            if not user:
                raise exception

            return user

    except ExpiredSignatureError:
        raise expired_exception  # Token expirado
    except InvalidTokenError:
        raise invalid_exception  # Token inválido

async def get_logged_admin(token: Annotated[str, Depends(oauth2_scheme)]):
    # Vai pegar o Token na Request, se válido
    # pegará o usuário no BD para confirmar e retornar ele
    exception = HTTPException(status_code=401, detail='Não autorizado!')
    invalid_exception = HTTPException(status_code=401, detail='Token inválido!')
    expired_exception = HTTPException(status_code=401, detail='Token expirado!')

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        email = payload.get('sub')

        if not email: 
            raise exception

        with Session(get_engine()) as session:
            sttm = select(Admin).where(Admin.email == email)
            admin = session.exec(sttm).first()

            if not admin:
                raise exception

            return admin

    except ExpiredSignatureError:
        raise expired_exception  # Token expirado
    except InvalidTokenError:
        raise invalid_exception  # Token inválido

# HASH Password
def hash_password(plain_password: str):
  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
  hash = pwd_context.hash(plain_password)
  return hash


def verify_hash(plain_password: str, hashed_password: str):
  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
  is_correct = pwd_context.verify(plain_password, hashed_password)
  return is_correct

def generate_token(sub: str, token_type: Literal['access', 'refresh']):
  expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRES)
  
  if token_type == 'refresh':
    expires = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_EXPIRES)
  
  token = jwt.encode({'sub': sub, 'exp': expires}, key=SECRET_KEY, algorithm=ALGORITHM)
  return token


def decode_token(token: str):
  payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
  return payload.get('sub')