from sqlmodel import SQLModel, Field

class BaseCarrinhoRevendedor(SQLModel):
    produto_codigo: int = Field(default=None, foreign_key="produto.id") 
    revendedor_id: int = Field(default=None, foreign_key="revendedor.id")
    quantidade: int = Field(default=1)
    
# Tabela Carrinho
class CarrinhoRevendedor(BaseCarrinhoRevendedor, table=True):
    id: int = Field(default=None, primary_key=True)
    status: bool = Field(default=False)  # Se esta em pedido ou não
    codigo: str = Field(default="") # Codigo de compra realizada com sucesso
    preco: float = Field(default=None)
    
class UpdateCarrinhoRevendedorRequest(BaseCarrinhoRevendedor):
    id: int
