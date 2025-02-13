from sqlmodel import SQLModel, Field
import datetime
from typing import List
from sqlalchemy.types import JSON
import json

class BasePedidoRevendedor(SQLModel):
    revendedor_id: int = Field(default=None, foreign_key="revendedor.id")
    opcao_de_pagamento: bool = Field(default=False) # False para pix e true para boleto
    

# Tabela pedido  
class PedidoRevendedor(BasePedidoRevendedor, table=True):
    id: int = Field(default=None, primary_key=True)
    criacao: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
    produtos: str = Field(default="[]", sa_column=JSON)
    status: bool = Field(default=True) # Se esperando pagamento ou cancelada
    pontos_fidelidade_resgatados: int
    total: float
    token_pagamento: str
    codigo: str # Se paga ou não
    frete: int = Field(default=0)
    cupom_de_desconto: str = Field(default="") # Se não for passado nenhum cupom fica vazio
    @property
    def tags_list(self) -> List[str]:
        return json.loads(self.tags)

    @tags_list.setter
    def tags_list(self, value: List[str]):
        self.tags = json.dumps(value)    
     
class UpdatePedidoRevendedorRequest(SQLModel):
    status: bool = Field(default=False) 
    pontos_fidelidade_resgatados: int
    cupom_de_desconto: str = Field(default="") # Se não for passado nenhum cupom fica vazio
    opcao_de_pagamento: bool = Field(default=False) # False para pix e true para boleto
    produtos: str = Field(default="[]", sa_column=JSON)
    status: bool = Field(default=True) # Se esperando pagamento ou cancelada
    total: float
    codigo: str # Se paga ou não
