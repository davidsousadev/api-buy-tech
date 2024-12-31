from sqlmodel import SQLModel, Field

class BaseCarrinho(SQLModel):
    produto_codigo: int = Field(default=None, foreign_key="product.id") 
    user_id: int = Field(default=None, foreign_key="user.id")
    quantidade: int = Field(default=1)
    
# Tabela Carrinho
class Carrinho(BaseCarrinho, table=True):
    id: int = Field(default=None, primary_key=True)
    status: bool = Field(default=False)  # Se esta zerado ou não
    codigo: str # Codigo de compra realizada com sucesso
    preco: float = Field(default=None)
class UpdateCarrinhoRequest(SQLModel):
    quantidade: int = Field(default=1)
