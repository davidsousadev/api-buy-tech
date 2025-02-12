from pydantic import BaseModel, Field

class Email(BaseModel):
    nome_remetente: str = Field(min_length=1)
    remetente: str = Field(min_length=1)
    destinatario: str = Field(min_length=1)
    assunto: str = Field(min_length=1)
    corpo: str = Field(min_length=1)
    senha: str = Field(min_length=1)

class SuporteEmail(BaseModel):
    enviar_email: str

class Equipamento(BaseModel):
    gabinete: str
    placaMae: str
    processador: str
    ram: str
    ssd: str
    fonte: str
    observacoes: str