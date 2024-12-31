from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_admin, get_logged_user
from src.database import get_engine
from src.models.vendas_models import BaseVenda, Venda, UpdateVendaRequest
from src.models.carrinho_models import Carrinho
from src.models.users_models import User
from src.models.admins_models import Admin
router = APIRouter()

@router.get("", response_model=List[Venda])
def listar_vendas(user: Annotated[User, Depends(get_logged_user)]):
    if not user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        statement = select(Venda)
        products = session.exec(statement).all()
        return products

@router.post("")
def cadastrar_venda(venda_data: BaseVenda,
                    user: Annotated[User, Depends(get_logged_user)]
                    ):
    if not user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
            
    with Session(get_engine()) as session:
        
        # Verifica se o cliente existe
        sttm = select(User).where(User.id == venda_data.user)
        cliente = session.exec(sttm).first()

        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado."
            )
        
        statement = select(Carrinho).where(Carrinho.user_id == user.id,
                                           Carrinho.status == False)
        itens = session.exec(statement).all()
        if not itens: 
           raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="O carrinho está vazio."
            ) 
        if itens:
            itens_carrinho=[]
            valor_items = 0
            for item in itens:
                itens_carrinho.append(item)
                valor_items += item.preco * item.quantidade

    venda = Venda(
        user=venda_data.user,
        produtos=f"{itens_carrinho}", 
        cupom_de_desconto=venda_data.cupom_de_desconto,
        status=False,
        total=valor_items
    )
    
    session.add(venda)
    session.commit()
    session.refresh(venda)
    return venda

    
@router.patch("/{venda_id}")
def atualizar_venda_por_id(
    venda_id: int,
    venda_data: UpdateVendaRequest,
    user: Annotated[User, Depends(get_logged_user)],
):
    if not user:
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
        statement = select(Carrinho).where(Carrinho.user_id == user.id,
                                           Carrinho.status == False)
        
        itens = session.exec(statement).all()
        if not itens: 
           raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="O carrinho está vazio."
            ) 
        if itens:
            itens_carrinho=[]
            valor_items = 0
            for item in itens:
                itens_carrinho.append(item.id)
                valor_items += item.preco * item.quantidade
        
        # Atualizar o status da venda
        if venda_data.status:
            venda_to_update.status = venda_data.status
        else: 
            venda_to_update.status = venda_data.status
            

        venda_to_update.produtos=f"{itens_carrinho}"
        venda_to_update.total=valor_items
            
        # Salvar as alterações no banco de dados
        session.add(venda_to_update)
        session.commit()
        session.refresh(venda_to_update)

        return {"message": "Venda com sucesso!", "venda": venda_to_update}
    
@router.get("/admin", response_model=List[Venda])
def listar_vendas(admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        statement = select(Venda)
        vendas = session.exec(statement).all()
        return vendas
    

@router.post("/admin")
def cadastrar_venda(venda_data: BaseVenda,
                    admin: Annotated[Admin, Depends(get_logged_admin)]
                    ):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
            
    with Session(get_engine()) as session:
        
        # Verifica se o cliente existe
        sttm = select(User).where(User.id == venda_data.user)
        cliente = session.exec(sttm).first()

        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado."
            )
        
        statement = select(Carrinho).where(Carrinho.user_id == venda_data.user,
                                           Carrinho.status == False)
        itens = session.exec(statement).all()
        if not itens: 
           raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="O carrinho está vazio."
            ) 
        if itens:
            itens_carrinho=[]
            valor_items = 0
            for item in itens:
                itens_carrinho.append(item)
                valor_items += item.preco * item.quantidade

    venda = Venda(
        user=venda_data.user,
        produtos=f"{itens_carrinho}", 
        cupom_de_desconto=venda_data.cupom_de_desconto,
        status=False,
        total=valor_items
    )
    
    session.add(venda)
    session.commit()
    session.refresh(venda)
    return venda

    
@router.patch("/admin/{venda_id}")
def atualizar_venda_por_id(
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
        statement = select(Carrinho).where(Carrinho.user_id == venda_data.user,
                                           Carrinho.status == False)
        
        itens = session.exec(statement).all()
        if not itens: 
           raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="O carrinho está vazio."
            ) 
        if itens:
            itens_carrinho=[]
            valor_items = 0
            for item in itens:
                itens_carrinho.append(item.id)
                valor_items += item.preco * item.quantidade
        
        # Atualizar o status da venda
        if venda_data.status:
            venda_to_update.status = venda_data.status
        else: 
            venda_to_update.status = venda_data.status
            

        venda_to_update.produtos=f"{itens_carrinho}"
        venda_to_update.total=valor_items
            
        # Salvar as alterações no banco de dados
        session.add(venda_to_update)
        session.commit()
        session.refresh(venda_to_update)

        return {"message": "Venda com sucesso!", "venda": venda_to_update}