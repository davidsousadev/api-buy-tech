from pydantic import BaseModel, Field
from datetime import date, datetime
import datetime
from sqlmodel import SQLModel, Field


    
class BaseCliente(SQLModel):
  nome: str
  email: str
  

# Criar cliente include BaseCliente
class SignUpClienteRequest(BaseCliente): 
  cpf: int      
  data_nascimento: str
  telefone: str       
  cep: int  
  complemento: str     
  password: str
  confirm_password: str
  
# Retorno dos dados
class ClienteData(BaseCliente):
  pontos_fidelidade: int
  clube_fidelidade: bool
  cod_indicacao: int
  status: bool
  admin: bool
  cpf: int      
  data_nascimento: str
  telefone: str       
  cep: int
  complemento: str  

# Include clientes
class IncludeCliente(BaseCliente): 
  cpf: int      
  data_nascimento: str
  telefone: str       
  cep: int 
  complemento: str
  
  
# Tabela clientes  
class Cliente(IncludeCliente, table=True):
  id: int = Field(default=None, primary_key=True)
  password: str
  criacao_de_conta: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
  pontos_fidelidade: float
  clube_fidelidade: bool
  cod_indicacao: int
  cod_confirmacao_email: str
  status: bool
  admin: bool = Field(default=False) 

# Login
class SignInClienteRequest(SQLModel):
  email: str
  password: str

class UpdateClienteRequest(BaseModel):
    nome: str | None = None
    email: str | None = None
    cpf: int | None = None
    data_nascimento: str | None = None
    telefone: str | None = None
    cep: int | None = None
    complemento: str | None = None
    password: str | None = None

# Lista de usuarios
class ClienteResponse(BaseModel):
    id: int
    nome: str  
    email: str
    cod_confirmacao_email: str
    criacao_de_conta: str
    pontos_fidelidade: int
    clube_fidelidade: bool
    cod_indicacao: int
    status: bool

    class Config:
        from_attributes = True