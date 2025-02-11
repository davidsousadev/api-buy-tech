from pydantic import Field
from datetime import datetime
import datetime
from sqlmodel import SQLModel, Field

class BaseCupom(SQLModel):
    nome: str
    valor: float = Field(default=1)
    tipo: bool = Field(default=False) # True para valor em reais e false para porcentagem
    quantidade_de_ultilizacao: int= Field(default=0) # Quantidade máxima de utilização
    
# Tabela Cupom de desconto  
class Cupom(BaseCupom, table=True):
    id: int = Field(default=None, primary_key=True)
    criacao: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
    resgatado: bool = Field(default=False) # Se já foi resgatado ou não, pois não pode ser atualizado depois de resgatado
    
class UpdateCupomRequest(BaseCupom):
    pass