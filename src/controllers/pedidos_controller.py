from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, and_
from src.auth_utils import get_logged_admin, get_logged_cliente
from src.database import get_engine
from src.models.pedidos_models import BasePedido, Pedido, UpdatePedidoRequest
from src.auth_utils import get_logged_cliente, get_logged_admin, hash_password
from src.models.carrinho_models import Carrinho
from src.models.produtos_models import Produto
from src.models.clientes_models import Cliente
from src.models.admins_models import Admin
from src.models.cupons_models import Cupom

from datetime import date, datetime
import datetime

from decouple import config
from davidsousa import enviar_email
from src.models.emails_models import Email
from src.html.email_pedido_realizado import template_pedido_realizado

EMAIL = config('EMAIL')
KEY_EMAIL = config('KEY_EMAIL')
URL= config('URL')

router = APIRouter()

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
            status_code=status.HTTP_403_FORBIDDEN,
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
   
@router.post("")
def cadastrar_pedido(
    pedido_data: BasePedido,
    cliente: Annotated[Cliente, Depends(get_logged_cliente)]
):
    if not cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        # Verifica se o cliente existe
        sttm = select(Cliente).where(Cliente.id == pedido_data.cliente)
        cliente = session.exec(sttm).first()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado."
            )

        # Verifica pedidos não pagos do cliente
        pedidos = select(Pedido).where(Pedido.cliente == cliente.id)
        pedidos_em_aberto = session.exec(pedidos).first()
        if pedidos_em_aberto and pedidos_em_aberto.status is False and pedidos_em_aberto.codigo == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cliente tem pedidos não pagos."
            )

        # Verifica os itens no carrinho do cliente
        statement = select(Carrinho).where(Carrinho.cliente_id == cliente.id)
        itens = session.exec(statement).all()
        if not itens:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="O carrinho está vazio."
            )

        # Inicializa variáveis para o cálculo do total
        itens_carrinho = []
        ids_itens_carrinho = []
        valor_items = 0
        quantidade = 0

        for item in itens:
            if item.status is False:
                # Verifica se o produto está disponível
                produto_sttm = select(Produto).where(Produto.id == item.produto_codigo)
                produto = session.exec(produto_sttm).first()
                if not produto:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Produto com código {item.produto_codigo} não encontrado."
                    )
                if produto.quantidade_estoque == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Produto '{produto.nome}' sem estoque!"
                    )
                if produto.quantidade_estoque < item.quantidade:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Quantidade solicitada para o produto '{produto.nome}' excede o estoque disponível!"
                    )

                # Atualiza variáveis
                quantidade += 1
                itens_carrinho.append(produto)
                ids_itens_carrinho.append(item.produto_codigo)
                valor_items += item.preco * item.quantidade 
       
        if quantidade == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Os itens do carrinho já estão em pedido."
            )

        # Aplica o cupom de desconto, se fornecido
        if pedido_data.cupom_de_desconto:
            statement = select(Cupom).where(Cupom.nome == pedido_data.cupom_de_desconto)
            cupom = session.exec(statement).first()
            if cupom:
                valor_cupom = cupom.valor
                tipo = cupom.tipo  # False para porcentagem, True para valor fixo

                if tipo is False:
                    desconto = valor_items * (valor_cupom / 100)
                else:
                    desconto = valor_cupom

                valor_items = max(valor_items - desconto, 0)
            else:
                pedido_data.cupom_de_desconto = ""
        else:
            pedido_data.cupom_de_desconto = ""

        # Cria o pedido
        pedido = Pedido(
            cliente=pedido_data.cliente,
            produtos=f"{ids_itens_carrinho}",
            cupom_de_desconto=pedido_data.cupom_de_desconto,
            status=True,
            codigo="",
            total=valor_items
        )
        session.add(pedido)
        session.commit()
        session.refresh(pedido)

        # Gera o código do pedido
        ano = datetime.datetime.now().strftime('%Y')
        codigo_pedido = hash_password(f"{ano}-{pedido_data.cliente}-{cliente.id}-buytech-{valor_items}")
        # Atualiza o status dos itens no carrinho para vinculá-los ao pedido
        for item in itens:
            if item.status is False:
                item.status = True
                session.add(item)
                session.commit()
                session.refresh(item)
        
        # Gera a URL de confirmação
        url = f"{URL}/vendas/confirmado/?codigo={codigo_pedido}"
        # Ajustar quantidades dos produtos, ajustas dados de envido dos produtos
        corpo_do_pedido = template_pedido_realizado(cliente.nome, (f"{ano}-{pedido_data.cliente}-{cliente.id}-buytech-{valor_items}"), url, valor_items, itens_carrinho)
        # Envia o e-mail de confirmação
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
            session.add(cliente)
            session.commit()
            session.refresh(cliente)
            return {"message": "Pedido realizado com sucesso! E-mail com dados enviado."}
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao enviar o e-mail de confirmação."
        )    
    

  
@router.patch("/{pedido_id}")
def cancelar_pedido_por_id(
    pedido_id: int,
    cliente: Annotated[Cliente, Depends(get_logged_cliente)],
):
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        # Selecionar o pedido
        pedidos_query = select(Pedido).where(Pedido.id == pedido_id, Pedido.cliente == cliente.id)
        pedido = session.exec(pedidos_query).first()
        
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não localizado!"
            )
        print(pedido.status)
        # Verificar condições do pedido
        if pedido.status and pedido.codigo == "":
            
            pedido.status = False
            produtos_ids = eval(pedido.produtos)  
            
            if isinstance(produtos_ids, list):
                produtos_query = select(Carrinho).where(Carrinho.cliente==cliente.id)
                produtos = session.exec(produtos_query).all()
                
                for produto in produtos:
                    produto.status = False
                    session.add(produto)
            
            # Salvar as alterações no banco de dados
            session.add(pedido)
            session.commit()
            session.refresh(pedido)
            
            return {"message": "Pedido e produtos cancelados com sucesso"}
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O pedido não pode ser cancelado!"
            )

@router.get("/admin", response_model=List[Pedido])
def listar_pedidos(
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
            status_code=status.HTTP_403_FORBIDDEN,
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
