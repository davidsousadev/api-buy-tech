from sqlmodel import SQLModel, Field

class CarrinhoBase(SQLModel):
    produto_codigo: int = Field(default=None, foreign_key="produto.id") 
    user_id: int = Field(default=None, foreign_key="user.id")
    quantidade: int = Field(default=1)
    
# Tabela Carrinho
class Carrinho(CarrinhoBase, table=True):
    id: int = Field(default=None, primary_key=True)
    status: bool = Field(default=True)
    codigo: int = Field(default=None)