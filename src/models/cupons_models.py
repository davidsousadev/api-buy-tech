from pydantic import Field
from datetime import datetime
import datetime
from sqlmodel import SQLModel, Field

class BaseCupom(SQLModel):
    name: str
    valor: float = Field(default=1)
    tipo: bool = Field(default=False)
    
# Tabela Cupom de desconto  
class Cupom(BaseCupom, table=True):
    id: int = Field(default=None, primary_key=True)
    criacao: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
    
    
class UpdateCupomRequest(BaseCupom):
    pass