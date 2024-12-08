from fastapi import APIRouter, status, HTTPException
from decouple import config
from davidsousa import enviar_email
from src.models import Email, EmailDados

EMAIL = config('EMAIL')
KEY_EMAIL = config('KEY_EMAIL')
KEY_POST_EMAIL= config('KEY_POST_EMAIL')

router = APIRouter()

@router.post('', status_code=status.HTTP_201_CREATED)
def enviar_email_base(envio_email: EmailDados):
    email = Email(
        nome_remetente = "Buy Tech",
        remetente = EMAIL,
        senha = KEY_EMAIL,
        destinatario = envio_email.destinatario,
        assunto = envio_email.assunto,
        corpo = envio_email.corpo,
        key = envio_email.key
        )

    if KEY_POST_EMAIL==envio_email.key:
        envio = enviar_email(
            email.nome_remetente, 
            email.remetente, 
            email.senha, 
            email.destinatario, 
            email.assunto, 
            email.corpo, 
            importante = True,
            html = True)
        if envio:
            return {"message": "E-mail enviado com sucesso!"}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Erro ao enviar e-mail"
    )