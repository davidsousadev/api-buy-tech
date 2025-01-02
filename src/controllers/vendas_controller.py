from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, and_
from src.auth_utils import get_logged_admin, get_logged_cliente
from src.database import get_engine
from src.models.pedidos_models import BasePedido, Pedido, UpdatePedidoRequest
from src.models.carrinho_models import Carrinho
from src.models.clientes_models import Cliente
from src.models.admins_models import Admin
from src.models.cupons_models import Cupom

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

    
@router.post("", response_model=BasePedido)
def cadastrar_pedido(pedido_data: BasePedido,
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
            
        pedidos = select(Pedido).where(Pedido.cliente==cliente.id)
        pedidos_em_aberto = session.exec(pedidos).first()
        
        if pedidos_em_aberto and (pedidos_em_aberto.status==True and pedidos_em_aberto.codigo==""):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente tem pedidos não pagos."
            )
    
        statement = select(Carrinho).where(Carrinho.cliente_idid == cliente.id)
        itens = session.exec(statement).all()
        if not itens: 
           raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="O carrinho está vazio."
            ) 
        if itens:
            itens_carrinho=[]
            ids_itens_carrinho=[]
            valor_items = 0
            quantidade=0
            for item in itens:
                if item.status==False:
                    quantidade+=1
                    itens_carrinho.append(item)
                    ids_itens_carrinho.append(item.produto_codigo)
                    valor_items += item.preco * item.quantidade
            if quantidade==0:
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Os itens do carrinho já estão em pedido."
            )
                          
                
        if pedido_data.cupom_de_desconto:        
            statement = select(Cupom).where(Cupom.nome == pedido_data.cupom_de_desconto)
            cupom = session.exec(statement).first()
            if cupom:
                valor_cupom = cupom.valor
                tipo = cupom.tipo

                if tipo is False:
                    desconto = valor_items * (valor_cupom / 100)
                else:
                    desconto = valor_cupom

                if desconto > valor_items:
                    valor_items = 0
                else:    
                    valor_items -= desconto
            else:
                pedido_data.cupom_de_desconto=""
        else:
            pedido_data.cupom_de_desconto="" 
               
        pedido = Pedido(
            cliente=pedido_data.cliente,
            produtos=f"{ids_itens_carrinho}", 
            cupom_de_desconto=pedido_data.cupom_de_desconto,
            status=False,
            code="",
            total=valor_items
        )
    
        session.add(pedido)
        session.commit()
        session.refresh(pedido)
        
        for item in itens:
            if item.status==False:
                item.status=True
                session.add(item)
                session.commit()
                session.refresh(item)
                        
        return pedido
  
@router.patch("/{pedido_id}")
def cancelar_pedido_por_id(
    pedido_id: int,
    pedido_data: UpdatePedidoRequest,
    cliente: Annotated[Cliente, Depends(get_logged_cliente)],
):
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        pedidos = select(pedidos).where(pedidos.id==pedido_id, pedido_data.cliente==cliente.id)
        pedidos_em_aberto = session.exec(pedidos).first()
        
        if pedidos_em_aberto.status==True and pedidos_em_aberto.codigo=="":
            # Atualizar o status da pedido
                pedidos_em_aberto.status = False
        
        
                # Salvar as alterações no banco de dados
                session.add(pedidos_em_aberto)
                session.commit()
                session.refresh(pedidos_em_aberto)

                return {"message": "pedido cancelada com sucesso"}

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
