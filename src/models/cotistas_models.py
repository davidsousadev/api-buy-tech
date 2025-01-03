from pydantic import BaseModel, Field
from datetime import date, datetime
import datetime
from sqlmodel import SQLModel, Field  
    
class BaseCotista(SQLModel):
  cliente: int = Field(default=None, foreign_key="cliente.id")
  saldo: float
  
# Criar cotista include BaseCotista
class SignUpCotistaRequest(BaseCotista): 
  salto: float
  
# Retorno dos dados
class CotistaData(BaseCotista):
  pass 

# Include cotistas
class IncludeCotista(BaseCotista): 
  pass
  
# Tabela cotistas  
class Cotista(IncludeCotista, table=True):
  id: int = Field(default=None, primary_key=True)
  criacao_de_conta: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
  status: bool

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