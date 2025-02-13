import string, random
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, and_, func
from src.auth_utils import get_logged_admin, get_logged_revendedor
from src.database import get_engine
from src.models.pedidos_revendedor_models import BasePedidoRevendedor, PedidoRevendedor, UpdatePedidoRevendedorRequest
from src.auth_utils import get_logged_revendedor, get_logged_admin, hash_password
from src.models.carrinhos_revendedor_models import CarrinhoRevendedor
from src.models.produtos_models import Produto
from src.models.revendedores_models import Revendedor
from src.models.admins_models import Admin
from src.models.cupons_models import Cupom
from datetime import datetime, timedelta, timezone
from src.auth_utils import get_logged_revendedor, get_logged_admin, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
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

# Administradores lista pedidos dos revendedors
@router.get("/admin", response_model=List[PedidoRevendedor])
def listar_pedidos_admin(
    admin: Annotated[Admin, Depends(get_logged_admin)],
    id: int | None = None,
    produtos: str | None = None,
    total: float | None = None,
    cupom_de_desconto: str | None = None,
    criacao: str | None = None,
    revendedor: int | None = None,
    status: bool | None = None,
    codigo: str | None = None
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(PedidoRevendedor)
        filtros = []

        if id is not None:
            filtros.append(PedidoRevendedor.id == id)
        if produtos is not None:
            filtros.append(PedidoRevendedor.produtos == produtos)
        if total is not None:
            filtros.append(PedidoRevendedor.total == total)
        if cupom_de_desconto is not None:
            filtros.append(PedidoRevendedor.cupom_de_desconto == cupom_de_desconto)
        if criacao is not None:
            filtros.append(PedidoRevendedor.criacao == criacao)
        if revendedor is not None:
            filtros.append(PedidoRevendedor.revendedor_id == revendedor)
        if status is not None:
            filtros.append(PedidoRevendedor.status == status)
        if codigo is not None:
            filtros.append(PedidoRevendedor.codigo == codigo)
        
        if filtros:
            statement = statement.where(and_(*filtros))
    
        pedidos = session.exec(statement).all()
        return pedidos

# Lista pedidos dos revendedors
@router.get("", response_model=List[PedidoRevendedor])
def listar_pedidos(
    revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)],
    id: int | None = None,
    produtos: str | None = None,
    total: float | None = None,
    cupom_de_desconto: str | None = None,
    criacao: str | None = None,
    status: bool | None = None,
    codigo: str | None = None
):
    if not revendedor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(PedidoRevendedor).where(PedidoRevendedor.revendedor_id == revendedor.id)
        filtros = [PedidoRevendedor.revendedor_id == revendedor.id] 
        if id is not None:
            filtros.append(PedidoRevendedor.id == id)
        if produtos is not None:
            filtros.append(PedidoRevendedor.produtos == produtos)
        if total is not None:
            filtros.append(PedidoRevendedor.total == total)
        if cupom_de_desconto is not None:
            filtros.append(PedidoRevendedor.cupom_de_desconto == cupom_de_desconto)
        if criacao is not None:
            filtros.append(PedidoRevendedor.criacao == criacao)
        if status is not None:
            filtros.append(PedidoRevendedor.status == status)
        if codigo is not None:
            filtros.append(PedidoRevendedor.codigo == codigo)
        if filtros:
            statement = statement.where(and_(*filtros))
        pedidos = session.exec(statement).all()

        return pedidos

# Lista pedidos dos revendedors por id
@router.get("/{pedido_id}")
def listar_pedidos_por_id(
    revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)],
    pedido_id: int 
):
    if not revendedor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(PedidoRevendedor).where(PedidoRevendedor.revendedor == revendedor.id, PedidoRevendedor.id == pedido_id)
        pedido = session.exec(statement).first()
        if pedido:
            return pedido
        else:
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pedido invalido!"
        )

# Cadastra pedidos dos revendedors
@router.post("")
def cadastrar_PedidoRevendedor(
    pedido_data: BasePedidoRevendedor,
    revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)]
):
    if not revendedor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        print()
        # Verifica se o revendedor existe
        sttm = select(Revendedor).where(Revendedor.id == pedido_data.revendedor_id)
        revendedor = session.exec(sttm).first()
        if not revendedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Revendedor não encontrado."
            )

        # Verifica pedidos não pagos do revendedor
        pedidos = select(PedidoRevendedor).where(PedidoRevendedor.revendedor_id == revendedor.id)
        pedidos_do_revendedor = session.exec(pedidos).all()
        pedido_em_aberto = False
        for pedido in pedidos_do_revendedor:
            if PedidoRevendedor.status is True and len(PedidoRevendedor.codigo) != 6:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="revendedor tem pedidos não pagos."
                )
            if not PedidoRevendedor.status and not PedidoRevendedor.codigo:
                pedido_em_aberto = pedido

        # Verifica os itens no carrinho do revendedor
        statement = select(CarrinhoRevendedor).where(
            CarrinhoRevendedor.revendedor_id == revendedor.id, 
            CarrinhoRevendedor.status == False, 
            func.length(CarrinhoRevendedor.codigo) != 6
        )
        itens = session.exec(statement).all()
        if not itens:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
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
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Produto com código {item.produto_codigo} não encontrado."
                    )
                if produto.quantidade_estoque < item.quantidade:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Os itens do carrinho já estão em PedidoRevendedor."
            )

        # Aplica o cupom de desconto, se fornecido
        desconto = 0

        

        # Aplica pontos de fidelidade corretamente sem conversão desnecessária
        pontos_fidelidade_resgatados = min(revendedor.pontos_fidelidade, valor_items)
        valor_items -= pontos_fidelidade_resgatados
        revendedor.pontos_fidelidade -= pontos_fidelidade_resgatados
        session.add(revendedor)
        session.commit()
        cupom = "Sem"
        # Gera código de confirmação
        codigo_de_confirmacao = gerar_codigo_confirmacao()
        numero_do_pedido = f"{KEY_STORE}-{revendedor.id}-{round(valor_items, 2)}"
        codigo_pedido = hash_password(codigo_de_confirmacao)
        codigo_de_confirmacao_token = (
            f"{numero_do_pedido}-{pedido_data.opcao_de_pagamento}-"
            f"{codigo_de_confirmacao}-{cupom}-"
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
            pedido = PedidoRevendedor(
                revendedor_id=pedido_data.revendedor_id,
                produtos=f"{ids_itens_carrinho}",
                pontos_fidelidade_resgatados=pontos_fidelidade_resgatados,
                status=True,
                opcao_de_pagamento=pedido_data.opcao_de_pagamento,
                codigo=codigo_pedido,
                token_pagamento=token_pagamento,
                total=round(valor_items, 2)
            )
            session.add(pedido)
        else:
            # Atualiza pedido em aberto
            pedido_em_aberto.produtos = f"{ids_itens_carrinho}"
            
            pedido_em_aberto.status = True
            pedido_em_aberto.criacao = datetime.now().strftime('%Y-%m-%d')
            
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
            revendedor.razao_social, 
            numero_do_pedido, 
            url_pagamento, 
            itens_carrinho, 
            0,
            pedido_data.opcao_de_pagamento,
            desconto, 
            "Sem cupom", 
            pontos_fidelidade_resgatados
        )

        email = Email(
            nome_remetente="Buy Tech",
            remetente=EMAIL,
            senha=KEY_EMAIL,
            destinatario=revendedor.email,
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

# Cancelar pedidos dos revendedors                     
@router.patch("/{pedido_id}")
def cancelar_pedido_por_id(
    pedido_id: int,
    revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)],
):
    if not revendedor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        # Selecionar o pedido
        pedidos_query = select(PedidoRevendedor).where(PedidoRevendedor.id == pedido_id, PedidoRevendedor.revendedor_id == revendedor.id)
        pedido = session.exec(pedidos_query).first()

        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não localizado!"
            )
        # Reverter possível uso de pontos de fidelidade
        if PedidoRevendedor.pontos_fidelidade_resgatados != 0:
            sttm = select(Revendedor).where(Revendedor.id == pedido.revendedor_id)
            revendedor_db = session.exec(sttm).first()
            if not revendedor_db:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="revendedor não pode cancelar pedido de outro revendedor."
                )
            revendedor_db.pontos_fidelidade += pedido.pontos_fidelidade_resgatados
            session.add(revendedor_db)
            session.commit()
            session.refresh(pedido)

        # Verificar condições do pedido para cancelamento
        if pedido.status and len(pedido.codigo) != 6:
            pedido.codigo = ""
            pedido.status = False
            produtos_ids = eval(pedido.produtos)
            
            if isinstance(produtos_ids, list):
                produtos_query = select(CarrinhoRevendedor).where(CarrinhoRevendedor.revendedor_id == revendedor.id)
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O pedido não pode ser cancelado, pois já foi cancelado anteriormente!"
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O pedido não pode ser cancelado, pois foi pago!"
            )

# Admin Cancela pedidos dos revendedors                     
@router.patch("/admin/{pedido_id}")
def cancelar_pedido_por_id_admin(
    pedido_id: int,
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        # Selecionar o pedido
        pedidos_query = select(PedidoRevendedor).where(PedidoRevendedor.id == pedido_id)
        pedido = session.exec(pedidos_query).first()

        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não localizado!"
            )
        # Reverter possível uso de pontos de fidelidade
        if pedido.pontos_fidelidade_resgatados != 0:
            sttm = select(Revendedor).where(Revendedor.id == pedido.revendedor_id)
            revendedor_db = session.exec(sttm).first()
            if not revendedor_db:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="revendedor não pode cancelar pedido de outro revendedor."
                )
            revendedor_db.pontos_fidelidade += pedido.pontos_fidelidade_resgatados
            session.add(revendedor_db)
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
                produtos_query = select(CarrinhoRevendedor).where(CarrinhoRevendedor.revendedor_id == pedido.revendedor_id)
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O pedido não pode ser cancelado, pois já foi cancelado anteriormente!"
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O pedido não pode ser cancelado, pois foi pago!"
            )
