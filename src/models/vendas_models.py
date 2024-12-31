from sqlmodel import SQLModel, Field
import datetime
from typing import List
from sqlalchemy.types import JSON
import json

class BaseVenda(SQLModel):
    user: int = Field(default=None, foreign_key="user.id")
    cupom_de_desconto: str = Field(default="") # Se não for passado nenhum cupom fica vazio
    

# Tabela Venda  
class Venda(BaseVenda, table=True):
    id: int = Field(default=None, primary_key=True)
    criacao: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
    produtos: str = Field(default="[]", sa_column=JSON)
    status: bool = Field(default=False) 
    total: float
    
    @property
    def tags_list(self) -> List[str]:
        return json.loads(self.tags)

    @tags_list.setter
    def tags_list(self, value: List[str]):
        self.tags = json.dumps(value)    
     
class UpdateVendaRequest(BaseVenda):
    status: bool = Field(default=False) 
