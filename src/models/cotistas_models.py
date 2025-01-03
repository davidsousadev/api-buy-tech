from pydantic import BaseModel, Field
from datetime import date, datetime
import datetime
from sqlmodel import SQLModel, Field
    
    
"""

id
id_cliente
saldo
status

"""    
    
class BaseCotista(SQLModel):
  nome: str
  email: str
  
# Criar cotista include BaseCotista
class SignUpCotistaRequest(BaseCotista): 
  cpf: int      
  data_nascimento: str
  telefone: str       
  cep: int       
  password: str
  confirm_password: str
  
# Retorno dos dados
class CotistaData(BaseCotista):
  pontos_fidelidade: int
  clube_fidelidade: bool
  cod_indicacao: int
  status: bool
  admin: bool
  cpf: int      
  data_nascimento: str
  telefone: str       
  cep: int  

# Include cotistas
class IncludeCotista(BaseCotista): 
  cpf: int      
  data_nascimento: str
  telefone: str       
  cep: int 
  
# Tabela cotistas  
class Cotista(IncludeCotista, table=True):
  id: int = Field(default=None, primary_key=True)
  password: str
  criacao_de_conta: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
  pontos_fidelidade: int
  clube_fidelidade: bool
  cod_indicacao: int
  cod_confirmacao_email: str
  status: bool
  admin: bool = Field(default=False) 

# Login
class SignInCotistaRequest(SQLModel):
  email: str
  password: str

class UpdateCotistaRequest(BaseModel):
    nome: str | None = None
    email: str | None = None
    cpf: int | None = None
    data_nascimento: str | None = None
    telefone: str | None = None
    cep: int | None = None
    password: str | None = None

# Lista de usuarios
class CotistaResponse(BaseModel):
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