from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_admin, get_logged_user
from src.database import get_engine
from src.models.users_models import User
from src.models.carrinho_models import Carrinho, BaseCarrinho, UpdateCarrinhoRequest
from src.models.products_models import Product

router = APIRouter()

@router.get("", response_model=List[Carrinho])
def listar_carrinho(
    
    user: Annotated[User, Depends(get_logged_user)]
                    ):
    
    if not user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
            
    with Session(get_engine()) as session:
        statement = select(Carrinho).where(Carrinho.user_id == user.id,
                                           Carrinho.status == False)
        itens = session.exec(statement).all()
        return itens

@router.post("", response_model=BaseCarrinho)
def cadastrar_item_carrinho(carrinho_data: BaseCarrinho,
                            user: Annotated[User, Depends(get_logged_user)]):
    if not user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
       
    with Session(get_engine()) as session:
        
        # Verifica se o produto existe
        sttm = select(Product).where(Product.id == carrinho_data.produto_codigo)
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
            
        if carrinho_data.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não pode adicionar itens no carrinho de outro usuário."
            )
        
        # Verifica se o cliente existe
        sttm = select(User).where(User.id == carrinho_data.user_id)
        cliente = session.exec(sttm).first()

        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )
            
        # Verifica se o produto já está no carrinho
        sttm = select(Carrinho).where(Carrinho.user_id == user.id, Carrinho.produto_codigo == carrinho_data.produto_codigo)
        carrinho = session.exec(sttm).first()
        if carrinho and carrinho.status==False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item já está no carrinho!"
            )
           
        if not (carrinho and carrinho.status==True):
            
            carrinho = Carrinho(
                produto_codigo=carrinho_data.produto_codigo,
                user_id=carrinho_data.user_id,
                quantidade=carrinho_data.quantidade,
                codigo="",
                status=False,
                preco=produto.preco
            )
        else:
            carrinho.preco=produto.preco
            carrinho.status=False
            
        session.add(carrinho)
        session.commit()
        session.refresh(carrinho)
        return carrinho


@router.patch("/{item_id}")
def atualizar_item_no_carrinho_por_id(
    item_id: int,
    carrinho_data: UpdateCarrinhoRequest,
    user: Annotated[User, Depends(get_logged_user)]
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        # Verifica se o produto existe
        sttm = select(Product).where(Product.id == item_id)
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
                detail="Item não pode ser atualizado."
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
        