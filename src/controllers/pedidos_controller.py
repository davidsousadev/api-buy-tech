import string, random
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, and_, func
from src.auth_utils import get_logged_admin, get_logged_cliente
from src.database import get_engine
from src.models.pedidos_models import BasePedido, Pedido
from src.auth_utils import get_logged_cliente, get_logged_admin, hash_password
from src.models.carrinhos_models import Carrinho
from src.models.produtos_models import Produto
from src.models.clientes_models import Cliente
from src.models.admins_models import Admin
from src.models.cupons_models import Cupom
from datetime import datetime, timedelta, timezone
from src.auth_utils import get_logged_cliente, get_logged_admin, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
import jwt
from datetime import datetime, timedelta, timezone
from decouple import config
from davidsousa import enviar_email
from src.models.emails_models import Email
from src.html.email_pedido_realizado import template_pedido_realizado

EMAIL = config('EMAIL')
KEY_EMAIL = config('KEY_EMAIL')
URL= config('URL')
KEY_STORE = config('KEY_STORE')

router = APIRouter()

# Gera codigo com 6 caracteres para confirmação
def gerar_codigo_confirmacao(tamanho=6):
        """Gera um código aleatório de confirmação."""
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choices(caracteres, k=tamanho))

# Lista os verbos disponiveis para esse controller
@router.options("", status_code=status.HTTP_200_OK)
async def options_pedidos():
    return { "methods": ["GET", "POST", "PATCH"] }

# Administradores lista pedidos dos clientes
@router.get("/admin", response_model=List[Pedido])
def listar_pedidos_admin(
    admin: Annotated[Admin, Depends(get_logged_admin)],
    id: int | None = None,
    produtos: str | None = None,
    total: float | None = None,
    cupom_de_desconto: str | None = None,
    criacao: str | None = None,
    cliente: int | None = None,
    status: bool | None = None,
    codigo: str | None = None
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(Pedido)
        filtros = []

        if id is not None:
            filtros.append(Pedido.id == id)
        if produtos is not None:
            filtros.append(Pedido.produtos == produtos)
        if total is not None:
            filtros.append(Pedido.total == total)
        if cupom_de_desconto is not None:
            filtros.append(Pedido.cupom_de_desconto == cupom_de_desconto)
        if criacao is not None:
            filtros.append(Pedido.criacao == criacao)
        if cliente is not None:
            filtros.append(Pedido.cliente == cliente)
        if status is not None:
            filtros.append(Pedido.status == status)
        if codigo is not None:
            filtros.append(Pedido.codigo == codigo)
        
        if filtros:
            statement = statement.where(and_(*filtros))
    
        pedidos = session.exec(statement).all()
        return pedidos

# Lista pedidos dos clientes
@router.get("", response_model=List[Pedido])
def listar_pedidos(
    cliente: Annotated[Cliente, Depends(get_logged_cliente)],
    id: int | None = None,
    produtos: str | None = None,
    total: float | None = None,
    cupom_de_desconto: str | None = None,
    criacao: str | None = None,
    status: bool | None = None,
    codigo: str | None = None
):
    if not cliente.id:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(Pedido).where(Pedido.cliente == cliente.id)
        filtros = [Pedido.cliente == cliente.id] 
        if id is not None:
            filtros.append(Pedido.id == id)
        if produtos is not None:
            filtros.append(Pedido.produtos == produtos)
        if total is not None:
            filtros.append(Pedido.total == total)
        if cupom_de_desconto is not None:
            filtros.append(Pedido.cupom_de_desconto == cupom_de_desconto)
        if criacao is not None:
            filtros.append(Pedido.criacao == criacao)
        if status is not None:
            filtros.append(Pedido.status == status)
        if codigo is not None:
            filtros.append(Pedido.codigo == codigo)
        if filtros:
            statement = statement.where(and_(*filtros))
        pedidos = session.exec(statement).all()

        return pedidos

# Lista pedidos dos clientes por id
@router.get("/{pedido_id}")
def listar_pedidos_por_id(
    cliente: Annotated[Cliente, Depends(get_logged_cliente)],
    pedido_id: int 
):
    if not cliente.id:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(Pedido).where(Pedido.cliente == cliente.id, Pedido.id == pedido_id)
        pedido = session.exec(statement).first()
        if pedido:
            return pedido
        else:
            raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Pedido invalido!"
        )

# Cadastra pedidos dos clientes
@router.post("")
def cadastrar_pedido(
    pedido_data: BasePedido,
    cliente: Annotated[Cliente, Depends(get_logged_cliente)]
):
    if not cliente.id:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        # Verifica se o cliente existe
        sttm = select(Cliente).where(Cliente.id == pedido_data.cliente)
        cliente = session.exec(sttm).first()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Cliente não encontrado."
            )

        # Verifica pedidos não pagos do cliente
        pedidos = select(Pedido).where(Pedido.cliente == cliente.id)
        pedidos_do_cliente = session.exec(pedidos).all()
        pedido_em_aberto = False
        for pedido in pedidos_do_cliente:
            if pedido.status is True and len(pedido.codigo) != 6:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail="Cliente tem pedidos não pagos."
                )
            if not pedido.status and not pedido.codigo:
                pedido_em_aberto = pedido

        # Verifica os itens no carrinho do cliente
        statement = select(Carrinho).where(
            Carrinho.cliente_id == cliente.id, 
            Carrinho.status == False, 
            func.length(Carrinho.codigo) != 6
        )
        itens = session.exec(statement).all()
        if not itens:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="O carrinho está vazio."
            )

        # Inicializa variáveis para o cálculo do total como float
        itens_carrinho = []
        ids_itens_carrinho = []
        valor_items = 0.0

        for item in itens:
            if not item.status:
                produto_sttm = select(Produto).where(Produto.id == item.produto_codigo)
                produto = session.exec(produto_sttm).first()
                if not produto:
                    raise HTTPException(
                        status_code=status.HTTP_204_NO_CONTENT,
                        detail=f"Produto com código {item.produto_codigo} não encontrado."
                    )
                if produto.quantidade_estoque < item.quantidade:
                    raise HTTPException(
                        status_code=status.HTTP_204_NO_CONTENT,
                        detail=f"Quantidade solicitada para o produto '{produto.nome}' excede o estoque disponível!"
                    )
                # Realiza a multiplicação com ponto flutuante
                valor_items += item.preco * item.quantidade
                itens_carrinho.append({
                    "nome": produto.nome,
                    "quantidade": item.quantidade,
                    "preco": item.preco
                })
                ids_itens_carrinho.append(item.produto_codigo)

        if valor_items == 0:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Os itens do carrinho já estão em pedido."
            )

        # Aplica o cupom de desconto, se fornecido
        desconto = 0.0

        # Acrescimo do frete (presumindo que pedido_data.frete seja um float)
        valor_items += pedido_data.frete

        if pedido_data.cupom_de_desconto:
            statement = select(Cupom).where(Cupom.nome == pedido_data.cupom_de_desconto)
            cupom = session.exec(statement).first()
            if cupom:
                if cupom.quantidade_de_ultilizacao == 0:
                    raise HTTPException(
                        status_code=status.HTTP_204_NO_CONTENT,
                        detail="A quantidade máxima de cupons já foi resgatada."
                    )
                valor_cupom = cupom.valor  # Pode ser float
                tipo = cupom.tipo  # False para porcentagem, True para valor fixo

                if tipo is False:
                    desconto = valor_items * (valor_cupom / 100)
                else:
                    desconto = valor_cupom
                valor_items = max(valor_items - desconto, 0)
            else:
                pedido_data.cupom_de_desconto = ""

        # Aplica pontos de fidelidade corretamente sem conversão desnecessária
        pontos_fidelidade_resgatados = min(cliente.pontos_fidelidade, valor_items)
        valor_items -= pontos_fidelidade_resgatados
        cliente.pontos_fidelidade -= pontos_fidelidade_resgatados
        session.add(cliente)
        session.commit()

        # Gera código de confirmação
        codigo_de_confirmacao = gerar_codigo_confirmacao()
        numero_do_pedido = f"{KEY_STORE}-{cliente.id}-{round(valor_items, 2)}"
        codigo_pedido = hash_password(codigo_de_confirmacao)
        codigo_de_confirmacao_token = (
            f"{numero_do_pedido}-{pedido_data.opcao_de_pagamento}-"
            f"{codigo_de_confirmacao}-{pedido_data.cupom_de_desconto}-"
            f"{pontos_fidelidade_resgatados}"
        )

        # Gera token de pagamento
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_EXPIRES if pedido_data.opcao_de_pagamento else REFRESH_EXPIRES
        )
        token_pagamento = jwt.encode(
            {'sub': codigo_de_confirmacao_token, 'exp': expires_at},
            key=SECRET_KEY,
            algorithm=ALGORITHM
        )

        url_pagamento = f"{URL}/operacoes/pagamentos/{token_pagamento}"

        # Cria ou atualiza o pedido
        if not pedido_em_aberto:
            # Criar novo pedido
            pedido = Pedido(
                cliente=pedido_data.cliente,
                produtos=f"{ids_itens_carrinho}",
                cupom_de_desconto=pedido_data.cupom_de_desconto,
                pontos_fidelidade_resgatados=pontos_fidelidade_resgatados,
                status=True,
                frete=pedido_data.frete,
                opcao_de_pagamento=pedido_data.opcao_de_pagamento,
                codigo=codigo_pedido,
                token_pagamento=token_pagamento,
                total=round(valor_items, 2)
            )
            session.add(pedido)
        else:
            # Atualiza pedido em aberto
            pedido_em_aberto.produtos = f"{ids_itens_carrinho}"
            pedido_em_aberto.frete = pedido_data.frete
            pedido_em_aberto.status = True
            pedido_em_aberto.criacao = datetime.now().strftime('%Y-%m-%d')
            pedido_em_aberto.cupom_de_desconto = pedido_data.cupom_de_desconto
            pedido_em_aberto.pontos_fidelidade_resgatados = pontos_fidelidade_resgatados
            pedido_em_aberto.opcao_de_pagamento = pedido_data.opcao_de_pagamento
            pedido_em_aberto.total = round(valor_items, 2)
            pedido_em_aberto.token_pagamento = token_pagamento
            pedido_em_aberto.codigo = codigo_pedido
            session.add(pedido_em_aberto)
        session.commit()

        # Atualiza status dos itens no carrinho
        for item in itens:
            if not item.status:
                item.status = True
                session.add(item)
        session.commit()

        # Envia e-mail de confirmação
        corpo_do_pedido = template_pedido_realizado(
            cliente.nome, 
            numero_do_pedido, 
            url_pagamento, 
            itens_carrinho, 
            pedido_data.frete,
            pedido_data.opcao_de_pagamento,
            desconto, 
            pedido_data.cupom_de_desconto, 
            pontos_fidelidade_resgatados
        )

        email = Email(
            nome_remetente="Buy Tech",
            remetente=EMAIL,
            senha=KEY_EMAIL,
            destinatario=cliente.email,
            assunto="Pedido - Buy Tech",
            corpo=corpo_do_pedido
        )
        envio = enviar_email(
            email.nome_remetente, 
            email.remetente, 
            email.senha, 
            email.destinatario, 
            email.assunto, 
            email.corpo, 
            importante=True, 
            html=True
        )

        if envio:
            return {"message": "Pedido realizado com sucesso! E-mail com dados enviado."}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao enviar o e-mail de confirmação."
            )

# Cancelar pedidos dos clientes                     
@router.patch("/{pedido_id}")
def cancelar_pedido_por_id(
    pedido_id: int,
    cliente: Annotated[Cliente, Depends(get_logged_cliente)],
):
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        # Selecionar o pedido
        pedidos_query = select(Pedido).where(Pedido.id == pedido_id, Pedido.cliente == cliente.id)
        pedido = session.exec(pedidos_query).first()

        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Pedido não localizado!"
            )
        # Reverter possível uso de pontos de fidelidade
        if pedido.pontos_fidelidade_resgatados != 0:
            sttm = select(Cliente).where(Cliente.id == pedido.cliente)
            cliente_db = session.exec(sttm).first()
            if not cliente_db:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail="Cliente não pode cancelar pedido de outro cliente."
                )
            cliente_db.pontos_fidelidade += pedido.pontos_fidelidade_resgatados
            session.add(cliente_db)
            session.commit()
            session.refresh(pedido)

        # Reverter possível uso de cupom de desconto
        if pedido.cupom_de_desconto != "":
            sttm = select(Cupom).where(Cupom.nome == pedido.cupom_de_desconto)
            cupom_de_desconto_resgatado = session.exec(sttm).first()
            if cupom_de_desconto_resgatado:
                cupom_de_desconto_resgatado.quantidade_de_ultilizacao += 1
                session.add(cupom_de_desconto_resgatado)
                session.commit()
                session.refresh(cupom_de_desconto_resgatado)

        # Verificar condições do pedido para cancelamento
        if pedido.status and len(pedido.codigo) != 6:
            pedido.codigo = ""
            pedido.status = False
            produtos_ids = eval(pedido.produtos)
            
            if isinstance(produtos_ids, list):
                produtos_query = select(Carrinho).where(Carrinho.cliente_id == cliente.id)
                produtos = session.exec(produtos_query).all()
                for produto in produtos:
                    produto.status = False
                    session.add(produto)
            
            session.add(pedido)
            session.commit()
            session.refresh(pedido)
            
            return {"message": "Pedido e produtos cancelados com sucesso"}
        
        if pedido and pedido.codigo == "":
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="O pedido não pode ser cancelado, pois já foi cancelado anteriormente!"
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="O pedido não pode ser cancelado, pois foi pago!"
            )

# Admin Cancela pedidos dos clientes                     
@router.patch("/admin/{pedido_id}")
def cancelar_pedido_por_id_admin(
    pedido_id: int,
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        # Selecionar o pedido
        pedidos_query = select(Pedido).where(Pedido.id == pedido_id)
        pedido = session.exec(pedidos_query).first()

        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Pedido não localizado!"
            )
        # Reverter possível uso de pontos de fidelidade
        if pedido.pontos_fidelidade_resgatados != 0:
            sttm = select(Cliente).where(Cliente.id == pedido.cliente)
            cliente_db = session.exec(sttm).first()
            if not cliente_db:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail="Cliente não pode cancelar pedido de outro cliente."
                )
            cliente_db.pontos_fidelidade += pedido.pontos_fidelidade_resgatados
            session.add(cliente_db)
            session.commit()
            session.refresh(pedido)

        # Reverter possível uso de cupom de desconto
        if pedido.cupom_de_desconto != "":
            sttm = select(Cupom).where(Cupom.nome == pedido.cupom_de_desconto)
            cupom_de_desconto_resgatado = session.exec(sttm).first()
            if cupom_de_desconto_resgatado:
                cupom_de_desconto_resgatado.quantidade_de_ultilizacao += 1
                session.add(cupom_de_desconto_resgatado)
                session.commit()
                session.refresh(cupom_de_desconto_resgatado)

        # Verificar condições do pedido para cancelamento
        if pedido.status and len(pedido.codigo) != 6:
            pedido.codigo = ""
            pedido.status = False
            produtos_ids = eval(pedido.produtos)
            
            if isinstance(produtos_ids, list):
                produtos_query = select(Carrinho).where(Carrinho.cliente_id == pedido.cliente)
                produtos = session.exec(produtos_query).all()
                for produto in produtos:
                    produto.status = False
                    session.add(produto)
            
            session.add(pedido)
            session.commit()
            session.refresh(pedido)
            
            return {"message": "Pedido e produtos cancelados com sucesso"}
        
        if pedido and pedido.codigo == "":
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="O pedido não pode ser cancelado, pois já foi cancelado anteriormente!"
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="O pedido não pode ser cancelado, pois foi pago!"
            )
