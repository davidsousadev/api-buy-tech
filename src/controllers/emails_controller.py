from fastapi import APIRouter, status, HTTPException
from decouple import config
from davidsousa import enviar_email
from src.models.emails_models import Email, SuporteEmail, Equipamento
from sqlmodel import Session, select
from src.database import get_engine
from src.models.clientes_models import Cliente
from src.models.admins_models import Admin
from src.models.revendedores_models import Revendedor
from src.html.email_redefinir_senha import template_redefinir_senha

from src.auth_utils import hash_password

EMAIL = config('EMAIL')
KEY_EMAIL = config('KEY_EMAIL')
URL= config('URL')

router = APIRouter()

import string
import random

# Gera codigo com 6 caracteres para confirmação
def gerar_codigo_confirmacao(tamanho=6):
        """Gera um código aleatório de confirmação."""
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choices(caracteres, k=tamanho))

# Lista os verbos disponiveis para esse controller
@router.options("", status_code=status.HTTP_200_OK)
async def options_emails():
    return { "methods": ["GET", "POST"] }

# Verifica se o email foi confirmado    
@router.get('/confirmado', status_code=status.HTTP_200_OK)
def email_confirmado(codigo: str):
    with Session(get_engine()) as session:
        clientes = select(Cliente).where(Cliente.cod_confirmacao_email == codigo)
        admins = select(Admin).where(Admin.cod_confirmacao_email == codigo)
        revendedores = select(Revendedor).where(Revendedor.cod_confirmacao_email == codigo)
        cliente_to_update = session.exec(clientes).first()
        admin_to_update = session.exec(admins).first()
        revendedor_to_update = session.exec(revendedores).first()

        if not cliente_to_update and not admin_to_update and not revendedor_to_update:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Codigo de recuperação invalido!"
            )
        if cliente_to_update:

            if cliente_to_update.cod_confirmacao_email=="Confirmado":
                raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="E-mail já confirmado."
                )  
            if len(cliente_to_update.cod_confirmacao_email)>6:
                cliente_to_update.email=codigo
                
            cliente_to_update.cod_confirmacao_email = "Confirmado"
            session.add(cliente_to_update)
            session.commit()
            session.refresh(cliente_to_update)    
            
        if admin_to_update:
            if admin_to_update.cod_confirmacao_email=="Confirmado":
                raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="E-mail já confirmado."
                )  
            if len(admin_to_update.cod_confirmacao_email)>6:
                admin_to_update.email=codigo
                
            admin_to_update.cod_confirmacao_email = "Confirmado"
            session.add(admin_to_update)
            session.commit()
            session.refresh(admin_to_update)

        if revendedor_to_update:
            if revendedor_to_update.cod_confirmacao_email=="Confirmado":
                raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="E-mail já confirmado."
                )  
            if len(revendedor_to_update.cod_confirmacao_email)>6:
                revendedor_to_update.email=codigo
                
            revendedor_to_update.cod_confirmacao_email = "Confirmado"
            session.add(revendedor_to_update)
            session.commit()
            session.refresh(revendedor_to_update)
            
        return {
                "email": True
                }
    
# Recuperar email
@router.get('/recuperar_email', status_code=status.HTTP_200_OK)
def recuperar_email(email: str | None = None, cpf: str | None = None, cnpj: str | None = None):
    with Session(get_engine()) as session:
        cliente_to_update = None
        admin_to_update = None

        if email:
            # Verificar em Cliente
            sttm_cliente = select(Cliente).where(Cliente.cod_confirmacao_email == email)
            cliente_to_update = session.exec(sttm_cliente).first()
            if cliente_to_update and len(cliente_to_update.cod_confirmacao_email) > 6:
                cliente_to_update.email = cliente_to_update.cod_confirmacao_email
            
            # Verificar em Admin
            sttm_admin = select(Admin).where(Admin.cod_confirmacao_email == email)
            admin_to_update = session.exec(sttm_admin).first()
            if admin_to_update and len(admin_to_update.cod_confirmacao_email) > 6:
                admin_to_update.email = admin_to_update.cod_confirmacao_email

            # Verificar em Revendedor
            sttm_revendedor = select(Revendedor).where(Revendedor.cod_confirmacao_email == email)
            revendedor_to_update = session.exec(sttm_revendedor).first()
            if revendedor_to_update and len(revendedor_to_update.cod_confirmacao_email) > 6:
                revendedor_to_update.email = revendedor_to_update.cod_confirmacao_email
            
            # Caso nenhum dos dois tenha correspondência
            if not cliente_to_update and not admin_to_update and not revendedor_to_update:
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="E-mail não está em recuperação!"
                )

        if cpf:
            # Verificar em Cliente
            sttm_cliente = select(Cliente).where(Cliente.cpf == cpf)
            cliente_to_update = session.exec(sttm_cliente).first()
            if cliente_to_update and len(cliente_to_update.cod_confirmacao_email) > 6:
                cliente_to_update.email = cliente_to_update.cod_confirmacao_email
            
            # Verificar em Admin
            sttm_admin = select(Admin).where(Admin.cpf == cpf)
            admin_to_update = session.exec(sttm_admin).first()
            if admin_to_update and len(admin_to_update.cod_confirmacao_email) > 6:
                admin_to_update.email = admin_to_update.cod_confirmacao_email
            
            # Caso nenhum dos dois tenha correspondência
            if not cliente_to_update and not admin_to_update:
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="CPF inválido!"
                )
        if cnpj:
            # Verificar em Revendedor
            sttm_revendedor = select(Revendedor).where(Revendedor.cnpj == cnpj)
            revendedor_to_update = session.exec(sttm_revendedor).first()
            if revendedor_to_update and len(revendedor_to_update.cod_confirmacao_email) > 6:
                revendedor_to_update.email = revendedor_to_update.cod_confirmacao_email
            
            # Caso nenhum dos dois tenha correspondência
            if not revendedor_to_update:
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="CNPJ inválido!"
                )
        # Atualizar e salvar no banco de dados
        if cliente_to_update:
            cliente_to_update.cod_confirmacao_email = "Confirmado"
            session.add(cliente_to_update)
            session.commit()
            session.refresh(cliente_to_update)

        if admin_to_update:
            admin_to_update.cod_confirmacao_email = "Confirmado"
            session.add(admin_to_update)
            session.commit()
            session.refresh(admin_to_update)
        if revendedor_to_update:
            revendedor_to_update.cod_confirmacao_email = "Confirmado"
            session.add(revendedor_to_update)
            session.commit()
            session.refresh(revendedor_to_update)

        # Retornar o sucesso
        if cliente_to_update or admin_to_update or revendedor_to_update:
            return {"email": True}
        else:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Nenhum registro foi atualizado!"
            )
 
# Recuperar senha
@router.get('/recuperar_senha', status_code=status.HTTP_200_OK)
def recuperar_senha(email: str | None = None):
    with Session(get_engine()) as session:
        if not email:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="E-mail é obrigatório!"
            )

        # Verificar se é um administrador
        sttm = select(Admin).where(Admin.email == email)
        admin_to_update = session.exec(sttm).first()

        if admin_to_update and admin_to_update.cod_confirmacao_email == "Confirmado":
            password = gerar_codigo_confirmacao()
            corpo_de_confirmacao = template_redefinir_senha(admin_to_update.nome, password)
            destinatario = admin_to_update.email
            entidade = admin_to_update
        else:
            # Verificar se é um usuário comum
            sttm = select(Cliente).where(Cliente.email == email)
            cliente_to_update = session.exec(sttm).first()

            if cliente_to_update and cliente_to_update.cod_confirmacao_email == "Confirmado":
                password = gerar_codigo_confirmacao()
                corpo_de_confirmacao = template_redefinir_senha(cliente_to_update.nome, password)
                destinatario = cliente_to_update.email
                entidade = cliente_to_update
            else:
                # Verificar se é um revendedor
                sttm = select(Revendedor).where(Revendedor.email == email)
                revendedor_to_update = session.exec(sttm).first()

                if revendedor_to_update and revendedor_to_update.cod_confirmacao_email == "Confirmado":
                    password = gerar_codigo_confirmacao()
                    corpo_de_confirmacao = template_redefinir_senha(revendedor_to_update.nome, password)
                    destinatario = revendedor_to_update.email
                    entidade = revendedor_to_update
                else:
                    raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="E-mail inválido!"
                    )

        # Configurar o e-mail
        email_data = Email(
            nome_remetente="Buy Tech",
            remetente=EMAIL,
            senha=KEY_EMAIL,
            destinatario=destinatario,
            assunto="Recuperar senha",
            corpo=corpo_de_confirmacao
        )

        # Enviar o e-mail
        envio = enviar_email(
            email_data.nome_remetente,
            email_data.remetente,
            email_data.senha,
            email_data.destinatario,
            email_data.assunto,
            email_data.corpo,
            importante=True,
            html=True
        )

        if envio:
            # Atualizar a senha no banco de dados
            entidade.password = hash_password(password)
            session.add(entidade)
            session.commit()
            session.refresh(entidade)
            return {"email": True}

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao enviar o e-mail"
        )

# E-mail para suporte
@router.post('/suporte/{cliente_id}', status_code=status.HTTP_200_OK)
def suporte_email(cliente_id: int, enviar_email_suporte: SuporteEmail):

    with Session(get_engine()) as session:

        if cliente_id:
            # Verificar em Cliente
            sttm_cliente = select(Cliente).where(Cliente.id == cliente_id)
            cliente_to_suporte = session.exec(sttm_cliente).first()
            if cliente_to_suporte:
                if cliente_to_suporte.cod_confirmacao_email=="Confirmado":
                    mensagem_ao_suporte = f"Sua Mensagem: {enviar_email_suporte.enviar_email}"
                   # Configurar o e-mail
                    email_data = Email(
                        nome_remetente="Buy Tech",
                        remetente=EMAIL,
                        senha=KEY_EMAIL,
                        destinatario=cliente_to_suporte.email,
                        assunto="Mensagem ao Suporte",
                        corpo=mensagem_ao_suporte
                    )
                    
                    # Enviar o e-mail
                    envio = enviar_email(
                        email_data.nome_remetente,
                        email_data.remetente,
                        email_data.senha,
                        email_data.destinatario,
                        email_data.assunto,
                        email_data.corpo,
                        importante=True,
                        html=True
                    )

                    if envio:

                        return {"mensage": "Contato recebido aguarde feedback!"}

                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Erro ao enviar o e-mail"
                    ) 
                else:
                    raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="Confirme o e-mail!"
                    )
        raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="Realize o cadastro!"
                    )
    
# Pedido Personalizado
@router.post('/monteSeuEquipamento/{cliente_id}', status_code=status.HTTP_200_OK)
def pedido_personalizado(cliente_id: int, equipamento: Equipamento):

    with Session(get_engine()) as session:

        if cliente_id:
            # Verificar em Cliente
            sttm_cliente = select(Cliente).where(Cliente.id == cliente_id)
            cliente_to_equipamento = session.exec(sttm_cliente).first()
            if cliente_to_equipamento:
                if cliente_to_equipamento.cod_confirmacao_email=="Confirmado":
                    pedido_personalizado = f"""
                        <html>
                        <head>
                            <style>
                                body {{
                                    font-family: Arial, sans-serif;
                                    margin: 0;
                                    padding: 0;
                                    background-color: #f4f4f4;
                                    color: #333;
                                }}
                                .container {{
                                    max-width: 600px;
                                    margin: 20px auto;
                                    padding: 20px;
                                    background-color: #fff;
                                    border-radius: 8px;
                                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                                }}
                                .header {{
                                    text-align: center;
                                    background-color: #4CAF50;
                                    color: white;
                                    padding: 10px 0;
                                    border-radius: 8px 8px 0 0;
                                }}
                                .content {{
                                    padding: 20px;
                                    font-size: 16px;
                                }}
                                .content p {{
                                    margin: 10px 0;
                                }}
                                .footer {{
                                    text-align: center;
                                    font-size: 12px;
                                    color: #777;
                                    padding-top: 20px;
                                    border-top: 1px solid #ddd;
                                }}
                                .label {{
                                    font-weight: bold;
                                }}
                                .value {{
                                    color: #555;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="header">
                                    <h2>Pedido Personalizado de {cliente_to_equipamento.nome}</h2>
                                </div>
                                <div class="content">
                                    <p><span class="label">Gabinete:</span> <span class="value">{equipamento.gabinete}</span></p>
                                    <p><span class="label">Placa-mãe:</span> <span class="value">{equipamento.placaMae}</span></p>
                                    <p><span class="label">Processador:</span> <span class="value">{equipamento.processador}</span></p>
                                    <p><span class="label">Memória RAM:</span> <span class="value">{equipamento.ram}</span></p>
                                    <p><span class="label">SSD:</span> <span class="value">{equipamento.ssd}</span></p>
                                    <p><span class="label">Fonte:</span> <span class="value">{equipamento.fonte}</span></p>
                                    <p><span class="label">Observações:</span> <span class="value">{equipamento.observacoes}</span></p>
                                </div>
                                <div class="footer">
                                    <p>Este é um e-mail automático, por favor não responda.</p>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                   # Configurar o e-mail
                    email_data = Email(
                        nome_remetente="Buy Tech",
                        remetente=EMAIL,
                        senha=KEY_EMAIL,
                        destinatario=cliente_to_equipamento.email,
                        assunto="Pedido Personalizado",
                        corpo=pedido_personalizado
                    )
                    
                    # Enviar o e-mail
                    envio = enviar_email(
                        email_data.nome_remetente,
                        email_data.remetente,
                        email_data.senha,
                        email_data.destinatario,
                        email_data.assunto,
                        email_data.corpo,
                        importante=True,
                        html=True
                    )

                    if envio:

                        return {"mensage": "Pedido recebido!"}

                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Erro ao enviar o e-mail"
                    ) 
                else:
                    raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="Confirme o e-mail!"
                    )
        raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="Realize o cadastro!"
                    )
