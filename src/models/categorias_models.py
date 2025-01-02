from pydantic import Field
from datetime import datetime
import datetime
from sqlmodel import SQLModel, Field

class BaseCategoria(SQLModel):
    nome: str = Field(..., min_length=5, description="A categoria deve ter no mínimo 5 letras.")
    
# Tabela Categoria  
class Categoria(BaseCategoria, table=True):
    id: int = Field(default=None, primary_key=True)
    criacao: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))