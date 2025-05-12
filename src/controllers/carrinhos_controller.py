from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, and_, func
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
    cliente: Annotated[Cliente, Depends(get_logged_cliente)]
):
    if not cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
    
    with Session(get_engine()) as session:
        statement = select(Carrinho).where(Carrinho.cliente_id == Cliente.id,
                                           Carrinho.status==False,
                                           func.length(Carrinho.codigo) == 0
                                           )   
        itens = session.exec(statement).all()
        if itens:
            return itens
        else:
            raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Carrinho vazio!"
        )

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
@router.post("", response_model=BaseCarrinho, status_code=status.HTTP_201_CREATED)
def cadastrar_item_carrinho(carrinho_data: BaseCarrinho,
                            cliente: Annotated[Cliente, Depends(get_logged_cliente)]):
    if not cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        # Verifica se o cliente existe
        sttm = select(Cliente).where(Cliente.id == carrinho_data.cliente_id)
        cliente = session.exec(sttm).first()

        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Usuário não encontrado."
            )
            
        if carrinho_data.cliente_id != cliente.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário não pode adicionar itens no carrinho de outro usuário."
            )
            
        # Verifica se o produto existe
        sttm = select(Produto).where(Produto.id == carrinho_data.produto_codigo)
        produto = session.exec(sttm).first()
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Produto não encontrado!"
            )
        if produto.quantidade_estoque == 0:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Produto sem estoque!"
            )
        if produto.quantidade_estoque < carrinho_data.quantidade:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Pedido maior que estoque!"
            )             
                
        # Verifica se o item já existe no carrinho
        sttm = select(Carrinho).where(
            Carrinho.cliente_id == cliente.id,
            Carrinho.produto_codigo == carrinho_data.produto_codigo
        )
        carrinho = session.exec(sttm).all()

        if carrinho:
            for item in carrinho:
                # Quantidade de Revendedor
                if item.quantidade >= 20:
                    raise HTTPException(
                        status_code=status.HTTP_200_OK,
                        detail="Cliente não pode adicionar mais de 20 itens no carrinho!"
                    )
                # Produto no carrinho, mas ainda não foi comprado
                if not item.status and item.quantidade != 0 and item.codigo == "":
                    raise HTTPException(
                        status_code=status.HTTP_200_OK,
                        detail="Item já está no carrinho!"
                    )
                # Produto está em pedido e não foi pago
                if item.status and item.quantidade != 0 and len(item.codigo) > 6:
                    raise HTTPException(
                        status_code=status.HTTP_200_OK,
                        detail="Item já está em pedido e não foi pago!"
                    )
                # Produto foi removido do carrinho, mas ainda pode ser recuperado
                if item.status and len(item.codigo) < 6:
                    item.status = False
                    item.quantidade = carrinho_data.quantidade
                    item.preco = produto.preco
                    session.add(item)
                    session.commit()
                    session.refresh(item)
                    return item

        # Adiciona um novo item ao carrinho
        if carrinho_data.quantidade >= 20:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Cliente não pode adicionar mais de 20 itens no carrinho!"
            )
        
        novo_carrinho = Carrinho(
            produto_codigo=carrinho_data.produto_codigo,
            cliente_id=carrinho_data.cliente_id,
            quantidade=carrinho_data.quantidade,
            codigo="",
            status=False,
            preco=produto.preco
        )

        session.add(novo_carrinho)
        session.commit()
        session.refresh(novo_carrinho)
        
        return novo_carrinho

# Atualizar itens no carrinho
@router.patch("/{carrinho_id}")
def atualizar_item_no_carrinho_por_id(
    carrinho_id: int,
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
        sttm = select(Produto).where(Produto.id == carrinho_data.produto_codigo)
        produto = session.exec(sttm).first()
        if not produto:
            raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="Produto não encontrado!"
                )
        if produto.quantidade_estoque==0:
            raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="Produto sem estoque!"
                )
        if produto.quantidade_estoque<carrinho_data.quantidade:
            raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="Pedido maior que estoque!"
                ) 
        if carrinho_data.quantidade >= 20:
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="Cliente não pode adicionar mais de 20 itens no carrinho!"
                )        
        sttm = select(Carrinho).where(Carrinho.id == carrinho_id)
        item_to_update = session.exec(sttm).first()

        if not item_to_update:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Item não encontrado."
            )
            
        if item_to_update.status==True and len(item_to_update.codigo) > 6:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Item não pode ser atualizado pois já esta em pedido."
            )
            
            
        if carrinho_data.quantidade==0 and len(item_to_update.codigo) == 0:
            item_to_update.status = True
            
            session.add(item_to_update)
            session.commit()
            session.refresh(item_to_update)
            
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Item removido do carrinho!"
            )
        
        # Atualizar os campos fornecidos
        if carrinho_data.quantidade!=0:
            item_to_update.quantidade = carrinho_data.quantidade
            item_to_update.status = False   
            
            session.add(item_to_update)
            session.commit()
            session.refresh(item_to_update)
            
            return {"message": "Item do carrinho atualizado com sucesso!", "carrinho": item_to_update}
        