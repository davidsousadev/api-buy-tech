from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, and_
from src.auth_utils import get_logged_admin, get_logged_cliente
from src.database import get_engine
from src.models.clientes_models import Cliente
from src.models.carrinhos_models import Carrinho, BaseCarrinho, UpdateCarrinhoRequest
from src.models.produtos_models import Produto
from src.models.admins_models import Admin

router = APIRouter()

# Lista os verbos disponiveis para esse controller
@router.options("", status_code=status.HTTP_200_OK)
async def options_carrinhos():
    return { "methods": ["GET", "POST", "PATCH"] }

# Clientes listar carrinhos
@router.get("", response_model=List[Carrinho])
def listar_carrinho(
    cliente: Annotated[Cliente, Depends(get_logged_cliente)],
    quantidade: int | None = None,
    preco: float | None = None,
    produto_codigo: int | None = None,
    codigo: str | None = None
):
    if not cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
    
    with Session(get_engine()) as session:
        statement = select(Carrinho).where(Carrinho.cliente_id == Cliente.id, Carrinho.status == False)
        filtros = [Carrinho.cliente_id == Cliente.id]
        
        if quantidade is not None:
            filtros.append(Carrinho.quantidade == quantidade)
        if preco is not None:
            filtros.append(Carrinho.preco == preco)
        if produto_codigo is not None:
            filtros.append(Carrinho.produto_codigo == produto_codigo)
        if codigo is not None:
            filtros.append(Carrinho.codigo == codigo)
        if filtros:
            statement = statement.where(and_(*filtros))
            
        itens = session.exec(statement).all()
        return itens

# Admins listar carrinhos
@router.get("/admin", response_model=List[Carrinho])
def listar_carrinhos_admin(
    admin: Annotated[Admin, Depends(get_logged_admin)],
    status: bool | None = None,
    codigo: str | None = None
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(Carrinho)
        filtros = []
        if status is not None:
            filtros.append(Carrinho.status == status)
        if codigo is not None:
            filtros.append(Carrinho.codigo == codigo)
        if filtros:
            statement = statement.where(and_(*filtros))
        itens = session.exec(statement).all()
        return itens

# Cadastrar itens no carrinho
@router.post("", response_model=BaseCarrinho)
def cadastrar_item_carrinho(carrinho_data: BaseCarrinho,
                            cliente: Annotated[Cliente, Depends(get_logged_cliente)]):
    if not cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
       
    with Session(get_engine()) as session:
        
        # Verifica se o produto existe
        sttm = select(Produto).where(Produto.id == carrinho_data.produto_codigo)
        produto = session.exec(sttm).first()
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado!"
            )
        if produto.quantidade_estoque==0:
            raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Produto sem estoque!"
                ) 
        if produto.quantidade_estoque<carrinho_data.quantidade:
            raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pedido maior que estoque!"
                ) 
            
        if carrinho_data.cliente_id != cliente.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não pode adicionar itens no carrinho de outro usuário."
            )
        
        # Verifica se o cliente existe
        sttm = select(Cliente).where(Cliente.id == carrinho_data.cliente_id)
        cliente = session.exec(sttm).first()

        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )
            
        # Verifica se o produto já está no carrinho
        sttm = select(Carrinho).where(Carrinho.cliente_id == cliente.id, Carrinho.produto_codigo == carrinho_data.produto_codigo)
        carrinho = session.exec(sttm).first()
        
        if carrinho and carrinho.status==False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item já está no carrinho!"
            )
           
        if carrinho and carrinho.status==True and carrinho.codigo=="":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item já está em pedido e não foi pago!"
            )
        if carrinho and carrinho.status==True and len(carrinho.codigo) > 6:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item já foi pago!"
            )
        else:
            carrinho = Carrinho(
                produto_codigo=carrinho_data.produto_codigo,
                cliente_id=carrinho_data.cliente_id,
                quantidade=carrinho_data.quantidade,
                codigo="",
                status=False,
                preco=produto.preco
                )
            
        session.add(carrinho)
        session.commit()
        session.refresh(carrinho)
        return carrinho

# Atualizar itens no carrinho
@router.patch("/{item_id}")
def atualizar_item_no_carrinho_por_id(
    item_id: int,
    carrinho_data: UpdateCarrinhoRequest,
    cliente: Annotated[Cliente, Depends(get_logged_cliente)]
):
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        # Verifica se o produto existe
        sttm = select(Produto).where(Produto.id == item_id)
        produto = session.exec(sttm).first()
        if not produto:
            raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Produto não encontrado!"
                )
        if produto.quantidade_estoque==0:
            raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Produto sem estoque!"
                )
        if produto.quantidade_estoque<carrinho_data.quantidade:
            raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pedido maior que estoque!"
                ) 
                
        sttm = select(Carrinho).where(Carrinho.id == item_id)
        item_to_update = session.exec(sttm).first()

        if not item_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não encontrado."
            )
            
        if item_to_update.status==True:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não pode ser atualizado pois já esta em pedido."
            )
            
        # Atualizar os campos fornecidos
        if carrinho_data.quantidade or carrinho_data.quantidade==0:

            if carrinho_data.quantidade>0:
                item_to_update.quantidade = carrinho_data.quantidade
                item_to_update.status = False
                    
            else:
                item_to_update.status = True
            
            # Salvar as alterações no banco de dados
            session.add(item_to_update)
            session.commit()
            session.refresh(item_to_update)
            return {"message": "Item atualizado com sucesso!", "carrinho": item_to_update}
        