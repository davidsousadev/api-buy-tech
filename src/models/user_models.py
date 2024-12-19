from pydantic import BaseModel, Field
from datetime import date, datetime
import datetime
from sqlmodel import SQLModel, Field


    
class BaseUser(SQLModel):
  name: str
  email: str
  

# Criar cliente include BaseUser
class SignUpUserRequest(BaseUser): 
  cpf: int      
  data_nascimento: str
  telefone: str       
  cep: int       
  password: str
  confirm_password: str
  
# Retorno dos dados
class UserData(BaseUser):
  pontos_fidelidade: int
  clube_fidelidade: bool
  cod_indicacao: int
  status: bool
  admin: bool
  cpf: int      
  data_nascimento: str
  telefone: str       
  cep: int  

# Include user
class IncludeUser(BaseUser): 
  cpf: int      
  data_nascimento: str
  telefone: str       
  cep: int 
  
# Tabela user  
class User(IncludeUser, table=True):
  id: int = Field(default=None, primary_key=True)
  password: str
  criacao_de_conta: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
  pontos_fidelidade: int
  clube_fidelidade: bool
  cod_indicacao: int
  status: bool
  admin: bool = Field(default=False) 

# Login
class SignInUserRequest(SQLModel):
  email: str
  password: str

class UpdateUserRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    cpf: int | None = None
    data_nascimento: str | None = None
    telefone: str | None = None
    cep: int | None = None
    password: str | None = None

# Lista de usuarios

class UserResponse(BaseModel):
    id: int
    name: str  
    email: str
    criacao_de_conta: str
    pontos_fidelidade: int
    clube_fidelidade: bool
    cod_indicacao: int
    status: bool

    class Config:
        from_attributes = True