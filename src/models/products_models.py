from pydantic import BaseModel, Field
from datetime import date, datetime
import datetime
from sqlmodel import SQLModel, Field
    
class BaseProduct(SQLModel):
    name: str
    preco: float
    foto: str
    marca: str
    categoria: int = Field(default=None, foreign_key=True)
    descricao: str
    quantidade_estoque: int
       
# Tabela Product  
class Product(BaseProduct, table=True):
    id: int = Field(default=None, primary_key=True)
    criacao: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
    status: str           
    personalizado: bool

class BaseCategoria(SQLModel):
    name: str
    
# Tabela Categoria  
class Categoria(BaseCategoria, table=True):
    id: int = Field(default=None, primary_key=True)
    criacao: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
    status: str           
    personalizado: bool