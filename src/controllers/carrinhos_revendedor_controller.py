from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, and_, func
from src.auth_utils import get_logged_admin, get_logged_revendedor
from src.database import get_engine
from src.models.revendedores_models import Revendedor
from src.models.carrinhos_revendedor_models import CarrinhoRevendedor, BaseCarrinhoRevendedor, UpdateCarrinhoRevendedorRequest
from src.models.produtos_models import Produto
from src.models.admins_models import Admin

router = APIRouter()

# Lista os verbos disponiveis para esse controller
@router.options("", status_code=status.HTTP_200_OK)
async def options_carrinhos():
    return { "methods": ["GET", "POST", "PATCH"] }

# revendedors listar carrinhos
@router.get("", response_model=List[CarrinhoRevendedor])
def listar_carrinho(
    revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)]
):
    if not revendedor.id:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )
    
    with Session(get_engine()) as session:
        statement = select(CarrinhoRevendedor).where(CarrinhoRevendedor.revendedor_id == CarrinhoRevendedor.id,
                                           CarrinhoRevendedor.status==False,
                                           func.length(CarrinhoRevendedor.codigo) == 0
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
@router.get("/admin", response_model=List[CarrinhoRevendedor])
def listar_carrinhos_admin(
    admin: Annotated[Admin, Depends(get_logged_admin)],
    status: bool | None = None,
    codigo: str | None = None
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(CarrinhoRevendedor)
        filtros = []
        if status is not None:
            filtros.append(CarrinhoRevendedor.status == status)
        if codigo is not None:
            filtros.append(CarrinhoRevendedor.codigo == codigo)
        if filtros:
            statement = statement.where(and_(*filtros))
        itens = session.exec(statement).all()
        return itens

# Cadastrar itens no carrinho
@router.post("", response_model=BaseCarrinhoRevendedor)
def cadastrar_item_carrinho(carrinho_data: BaseCarrinhoRevendedor,
                            revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)]):
    if not revendedor.id:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        # Verifica se o revendedor existe
        sttm = select(Revendedor).where(Revendedor.id == carrinho_data.revendedor_id)
        revendedor = session.exec(sttm).first()

        if not revendedor:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Usuário não encontrado."
            )
            
        if carrinho_data.revendedor_id != revendedor.id:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Usuário não pode adicionar itens no carrinho de outro usuário."
            )
            
        # Verifica se o produto existe
        sttm = select(Produto).where(Produto.id == carrinho_data.produto_codigo)
        produto = session.exec(sttm).first()
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Produto não encontrado!"
            )
        if produto.quantidade_estoque==0:
            raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail="Produto sem estoque!"
                ) 
        if produto.quantidade_estoque<carrinho_data.quantidade:
            raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail="Pedido maior que estoque!"
                )             
            
        sttm = select(CarrinhoRevendedor).where(
        CarrinhoRevendedor.revendedor_id == revendedor.id,
        CarrinhoRevendedor.produto_codigo == carrinho_data.produto_codigo
    )
    carrinho = session.exec(sttm).all()

    if carrinho:
        for item in carrinho:
            # Produto no CarrinhoRevendedor, mas ainda não foi comprado
            if not item.status and item.quantidade != 0 and item.codigo == "":
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail="Item já está no carrinho!"
                )

            # Produto está em pedido e não foi pago
            if item.status and item.quantidade != 0 and len(item.codigo) > 6:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail="Item já está em pedido e não foi pago!"
                )

            # Produto foi removido do CarrinhoRevendedor, mas ainda pode ser recuperado
            if item.status and len(item.codigo) < 6:
                item.status = False
                item.quantidade = carrinho_data.quantidade
                item.preco = produto.preco
                session.add(item)
                session.commit()
                session.refresh(item)
                return item

    # Adiciona um novo item ao carrinho
    novo_carrinho = CarrinhoRevendedor(
        produto_codigo=carrinho_data.produto_codigo,
        revendedor_id=carrinho_data.revendedor_id,
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
    carrinho_data: UpdateCarrinhoRevendedorRequest,
    revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)]
):
    if not revendedor:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        # Verifica se o produto existe
        sttm = select(Produto).where(Produto.id == carrinho_data.produto_codigo)
        produto = session.exec(sttm).first()
        if not produto:
            raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail="Produto não encontrado!"
                )
        if produto.quantidade_estoque==0:
            raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail="Produto sem estoque!"
                )
        if produto.quantidade_estoque<carrinho_data.quantidade:
            raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail="Pedido maior que estoque!"
                ) 
                
        sttm = select(CarrinhoRevendedor).where(CarrinhoRevendedor.id == carrinho_id)
        item_to_update = session.exec(sttm).first()

        if not item_to_update:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Item não encontrado."
            )
            
        if item_to_update.status==True and len(item_to_update.codigo) > 6:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Item não pode ser atualizado pois já esta em PedidoRevendedor."
            )
            
            
        if carrinho_data.quantidade==0 and len(item_to_update.codigo) == 0:
            item_to_update.status = True
            
            session.add(item_to_update)
            session.commit()
            session.refresh(item_to_update)
            
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
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
        