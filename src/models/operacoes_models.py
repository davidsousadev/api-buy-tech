from pydantic import BaseModel, Field
from datetime import date, datetime
import datetime
from sqlmodel import SQLModel, Field

"""

id 
cliente 
data
tipo
valor

"""

class BaseOperacao(SQLModel):
  cliente: int = Field(default=None, foreign_key="cliente.id")
  valor: float = Field(default=1)
  
# Tabela operacao  
class Operacao(BaseOperacao, table=True):
  id: int = Field(default=None, primary_key=True)
  criacao_da_operacao: str = Field(default=datetime.datetime.now().strftime('%Y-%m-%d'))
  motivo: int = Field(default=1) # 1 Referência 2 Cashback 3 Pagamento 
  tipo: int = Field(default=1) # 1 Credito 2 Debito
  codigo: str # Se for pagamento recebe o codigo do pagamento, se for indicacao recebe o codigo do indicado
