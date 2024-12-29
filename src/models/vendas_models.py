from sqlmodel import SQLModel, Field
import datetime

class BaseVenda(SQLModel):
    user: int = Field(default=None, foreign_key="user.id")
    produtos: int
    cupom_de_desconto: str = Field(default=None)
    pedido_personalizado: bool = Field(default=None)

# Tabela Venda  
class Venda(BaseVenda, table=True):
    id: int = Field(default=None, primary_key=True)
    criacao: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
    status: bool = Field(default=False) 
    total: float       
     
class UpdateVendaRequest(BaseVenda):
    status: bool = Field(default=False)
