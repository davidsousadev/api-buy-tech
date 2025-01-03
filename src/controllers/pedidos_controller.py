import string, random
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

def gerar_codigo_do_pedido(tamanho=6):
        """Gera um código aleatório de confirmação."""
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choices(caracteres, k=tamanho))

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
        if pedidos_em_aberto and pedidos_em_aberto.status is False and pedidos_em_aberto.codigo != "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cliente tem pedidos não pagos."
            )
        
        if pedidos_em_aberto and pedidos_em_aberto.status is False and pedidos_em_aberto.codigo == "":
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
                    itens_carrinho.append({
                        "nome": produto.nome,
                        "quantidade": item.quantidade,
                        "preco": item.preco
                        })
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

            # Aplicar pontos de fidelidade
            if valor_items > 0:
                pontos_fidelidade_resgatados = min(cliente.pontos_fidelidade, int(valor_items))
                valor_items -= pontos_fidelidade_resgatados
                cliente.pontos_fidelidade -= pontos_fidelidade_resgatados
                session.add(cliente)
                session.commit()
                session.refresh(cliente)

            codigo_de_confirmacao = gerar_codigo_do_pedido()
            numero_do_pedido=f"{KEY_STORE}-{cliente.id}-{valor_items}"
            codigo_pedido = hash_password(codigo_de_confirmacao)

            codigo_de_confirmacao_token = f"{numero_do_pedido}-{pedido_data.opcao_de_pagamento}-{codigo_de_confirmacao}"

            if pedido_data.opcao_de_pagamento==False: 
                # Tá tudo OK pode gerar um Token JWT e devolver
                expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRES)
                token_pix = jwt.encode({'sub': codigo_de_confirmacao_token, 'exp': expires_at}, key=SECRET_KEY, algorithm=ALGORITHM)

                # Gera  o link de pagamento
                url = f"{URL}/pagamentos/{token_pix}"

            if pedido_data.opcao_de_pagamento==True:    
                expires_rt = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_EXPIRES)
                token_boleto = jwt.encode({'sub': codigo_de_confirmacao_token, 'exp': expires_rt}, key=SECRET_KEY, algorithm=ALGORITHM)

                # Gera  o link de pagamento
                url = f"{URL}/pagamentos/{token_boleto}"

            # Definir pontos de fidelidade resgatados como 0 se não existirem
            pontos_resgatados = pontos_fidelidade_resgatados if pontos_fidelidade_resgatados else 0

            # Cria o pedido
            pedido_atualizado = Pedido(
                cliente=pedido_data.cliente,
                produtos=f"{ids_itens_carrinho}",
                cupom_de_desconto=pedido_data.cupom_de_desconto,
                pontos_fidelidade_resgatados=pontos_resgatados,
                status=True,
                opcao_de_pagamento=pedido_data.opcao_de_pagamento,
                codigo=codigo_pedido,
                total=valor_items
            )


            session.add(pedido_atualizado)
            session.commit()
            session.refresh(pedido_atualizado)

            # Atualiza o status dos itens no carrinho para vinculá-los ao pedido
            for item in itens:
                if item.status is False:
                    item.status = True
                    session.add(item)
                    session.commit()
                    session.refresh(item)

            # Definir valores padrão caso cupom ou pontos não existam
            nome_cupom = cupom.nome if cupom else None
            desconto = desconto if cupom else 0
            pontos_resgatados = pontos_fidelidade_resgatados if pontos_fidelidade_resgatados else 0

            # Ajustar quantidades dos produtos, ajustar dados de envio dos produtos
            corpo_do_pedido = template_pedido_realizado(
                cliente.nome,
                numero_do_pedido,
                url,
                valor_items,
                itens_carrinho,
                desconto,
                nome_cupom,
                pontos_resgatados
            )
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
         
            
        if not pedidos_em_aberto:
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
                    itens_carrinho.append({
                        "nome": produto.nome,
                        "quantidade": item.quantidade,
                        "preco": item.preco
                        })
                    
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
            
            # Aplicar pontos de fidelidade
            if valor_items > 0:
                pontos_fidelidade_resgatados = min(cliente.pontos_fidelidade, int(valor_items))
                valor_items -= pontos_fidelidade_resgatados
                cliente.pontos_fidelidade -= pontos_fidelidade_resgatados
                session.add(cliente)
                session.commit()
                session.refresh(cliente)

                
            codigo_de_confirmacao = gerar_codigo_do_pedido()
            numero_do_pedido=f"{KEY_STORE}-{cliente.id}-{valor_items}"
            codigo_pedido = hash_password(codigo_de_confirmacao)

            codigo_de_confirmacao_token = f"{numero_do_pedido}-{pedido_data.opcao_de_pagamento}-{codigo_de_confirmacao}"

            if pedido_data.opcao_de_pagamento==False: 
                # Tá tudo OK pode gerar um Token JWT e devolver
                expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRES)
                token_pix = jwt.encode({'sub': codigo_de_confirmacao_token, 'exp': expires_at}, key=SECRET_KEY, algorithm=ALGORITHM)

                # Gera  o link de pagamento
                url = f"{URL}/pagamentos/{token_pix}"

            if pedido_data.opcao_de_pagamento==True:    
                expires_rt = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_EXPIRES)
                token_boleto = jwt.encode({'sub': codigo_de_confirmacao_token, 'exp': expires_rt}, key=SECRET_KEY, algorithm=ALGORITHM)

                # Gera  o link de pagamento
                url = f"{URL}/pagamentos/{token_boleto}"

            # Definir pontos de fidelidade resgatados como 0 se não existirem
            pontos_resgatados = pontos_fidelidade_resgatados if pontos_fidelidade_resgatados else 0

            # Cria o pedido
            pedido = Pedido(
                cliente=pedido_data.cliente,
                produtos=f"{ids_itens_carrinho}",
                cupom_de_desconto=pedido_data.cupom_de_desconto,
                pontos_fidelidade_resgatados=pontos_resgatados,
                status=True,
                opcao_de_pagamento=pedido_data.opcao_de_pagamento,
                codigo=codigo_pedido,
                total=valor_items
            )

            

            session.add(pedido)
            session.commit()
            session.refresh(pedido)

            # Atualiza o status dos itens no carrinho para vinculá-los ao pedido
            for item in itens:
                if item.status is False:
                    item.status = True
                    session.add(item)
                    session.commit()
                    session.refresh(item)
                    
            # Definir valores padrão caso cupom ou pontos não existam
            nome_cupom = cupom.nome if cupom else None
            desconto = desconto if cupom else 0
            pontos_resgatados = pontos_fidelidade_resgatados if pontos_fidelidade_resgatados else 0

            # Ajustar quantidades dos produtos, ajustar dados de envio dos produtos
            corpo_do_pedido = template_pedido_realizado(
                cliente.nome,
                numero_do_pedido,
                url,
                valor_items,
                itens_carrinho,
                desconto,
                nome_cupom,
                pontos_resgatados
            )
            
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
        if pedido.pontos_fidelidade_resgatados != 0:
            # Verifica se o cliente existe
            sttm = select(Cliente).where(Cliente.id == cliente.id)
            cliente = session.exec(sttm).first()
            if not cliente:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cliente não encontrado."
                )
            if cliente:
                cliente.pontos_fidelidade += pedido.pontos_fidelidade_resgatados
                # Salvar as alterações no banco de dados
                session.add(pedido)
                session.commit()
                session.refresh(pedido)  
                  
        # Verificar condições do pedido
        if pedido.status and len(pedido.codigo) != 6:
            pedido.codigo = ""
            pedido.status = False
            produtos_ids = eval(pedido.produtos)  
            
            if isinstance(produtos_ids, list):
                produtos_query = select(Carrinho).where(Carrinho.cliente_id==cliente.id)
                produtos = session.exec(produtos_query).all()
                
                for produto in produtos:
                    produto.status = False
                    session.add(produto)
            
            # Salvar as alterações no banco de dados
            session.add(pedido)
            session.commit()
            session.refresh(pedido)
            
            return {"message": "Pedido e produtos cancelados com sucesso"}
        
        if pedido and pedido.codigo=="":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O pedido não pode ser cancelado, pois já foi cancelado anteriormente!"
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O pedido não pode ser cancelado, pois foi pago!"
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
