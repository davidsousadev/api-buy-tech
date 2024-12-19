from pydantic import BaseModel, Field
from datetime import date, datetime
import datetime
from sqlmodel import SQLModel, Field

class EmailDados(BaseModel):
    destinatario: str = Field(min_length=1)
    assunto: str = Field(min_length=1)
    corpo: str = Field(min_length=1)
    key: str = Field(min_length=1)
    
class Email(EmailDados):
    nome_remetente: str = Field(min_length=1)
    remetente: str = Field(min_length=1)
    senha: str = Field(min_length=1)