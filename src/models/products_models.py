from pydantic import Field
from datetime import datetime
import datetime
from sqlmodel import SQLModel, Field
    
class BaseProduct(SQLModel):
    name: str
    preco: float
    foto: str
    marca: str
    categoria: int = Field(default=None, foreign_key="categoria.id")
    descricao: str
    quantidade_estoque: int
    personalizado: bool = Field(default=False)  
       
# Tabela Product  
class Product(BaseProduct, table=True):
    id: int = Field(default=None, primary_key=True)
    criacao: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
    status: bool = Field(default=False)   # Se esta em promoção ou não     
    
class UpdateProductRequest(BaseProduct):
    status: bool = Field(default=False)