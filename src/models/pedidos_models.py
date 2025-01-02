from sqlmodel import SQLModel, Field
import datetime
from typing import List
from sqlalchemy.types import JSON
import json

class BasePedido(SQLModel):
    cliente: int = Field(default=None, foreign_key="cliente.id")
    cupom_de_desconto: str = Field(default="") # Se não for passado nenhum cupom fica vazio
    

# Tabela pedido  
class Pedido(BasePedido, table=True):
    id: int = Field(default=None, primary_key=True)
    criacao: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
    produtos: str = Field(default="[]", sa_column=JSON)
    status: bool = Field(default=True) # Se esperando pagamento ou cancelada
    total: float
    codigo: str = Field(default="") # Se paga ou não
    @property
    def tags_list(self) -> List[str]:
        return json.loads(self.tags)

    @tags_list.setter
    def tags_list(self, value: List[str]):
        self.tags = json.dumps(value)    
     
class UpdatePedidoRequest(BasePedido):
    status: bool = Field(default=False) 
