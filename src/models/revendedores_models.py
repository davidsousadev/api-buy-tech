from pydantic import BaseModel, Field
from datetime import datetime
import datetime
from sqlmodel import SQLModel, Field
   
class BaseRevendedor(SQLModel):
  razao_social: str
  email: str

# Criar Revendedor include BaseRevendedor
class SignUpRevendedorRequest(BaseRevendedor): 
  cnpj: int      
  telefone: str       
  inscricao_estadual: int 
  password: str
  confirm_password: str
  
# Retorno dos dados
class RevendedorData(BaseRevendedor):
  status: bool
  cnpj: int      
  inscricao_estadual: int 
  telefone: str       

# Include Revendedor
class IncludeRevendedor(BaseRevendedor): 
  cnpj: int      
  telefone: str       
  inscricao_estadual: int 
  
# Tabela Revendedor  
class Revendedor(IncludeRevendedor, table=True):
  id: int = Field(default=None, primary_key=True)
  password: str
  criacao_de_conta: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
  cod_confirmacao_email: str
  status: bool

# Login
class SignInRevendedorRequest(SQLModel):
  email: str
  password: str

class UpdateRevendedorRequest(BaseModel):
    razao_social: str | None = None
    email: str | None = None
    cnpj: int | None = None
    inscricao_estadual: int | None = None
    telefone: str | None = None
    password: str | None = None

# Lista de Revendedores
class RevendedorResponse(BaseModel):
    id: int
    razao_social: str  
    email: str
    cod_confirmacao_email: str
    criacao_de_conta: str
    status: bool

    class Config:
        from_attributes = True
        