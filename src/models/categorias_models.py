from pydantic import Field
from datetime import datetime
import datetime
from sqlmodel import SQLModel, Field

class BaseCategoria(SQLModel):
    name: str
    
# Tabela Categoria  
class Categoria(BaseCategoria, table=True):
    id: int = Field(default=None, primary_key=True)
    criacao: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))