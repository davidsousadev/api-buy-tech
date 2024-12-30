from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_admin, get_logged_user
from src.database import get_engine
from src.models.admins_models import Admin
from src.models.users_models import User
from src.models.carrinho_models import Carrinho, BaseCarrinho
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
        statement = select(Carrinho).where(Carrinho.user_id == user.id).where(Carrinho.status == False)
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
        item = session.exec(sttm).first()
        if item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item já está no carrinho!"
            )
        # Verifica se o produto existe
        sttm = select(Product).where(Product.id == carrinho_data.produto_codigo)
        produto = session.exec(sttm).first()
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado!"
            )
            
        total = produto.preco * carrinho_data.quantidade
        
        carrinho = Carrinho(
            produto_codigo=carrinho_data.produto_codigo,
            user_id=carrinho_data.user_id,
            quantidade=carrinho_data.quantidade,
            codigo=None,
            total=total
        )
        
        session.add(carrinho)
        session.commit()
        session.refresh(carrinho)
        return carrinho

""" 
@router.patch("/{venda_id}")
def atualizar_item_no_carrinho_por_id(
    venda_id: int,
    venda_data: UpdateVendaRequest,
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        sttm = select(Venda).where(Venda.id == venda_id)
        venda_to_update = session.exec(sttm).first()

        if not venda_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venda não encontrada."
            )
        
        # Atualizar os campos fornecidos
        if venda_data.status:
            venda_to_update.status = venda_data.status
        
            
        # Salvar as alterações no banco de dados
        session.add(venda_to_update)
        session.commit()
        session.refresh(venda_to_update)

        return {"message": "Venda com sucesso!", "venda": venda_to_update}
"""