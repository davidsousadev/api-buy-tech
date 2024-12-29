from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_admin, get_logged_user
from src.database import get_engine
from src.models.admins_models import Admin
from src.models.vendas_models import BaseVenda, Venda, UpdateVendaRequest
from src.models.users_models import User
router = APIRouter()

@router.get("", response_model=List[Venda])
def listar_vendas():
    with Session(get_engine()) as session:
        statement = select(Venda)
        products = session.exec(statement).all()
        return products

@router.post("", response_model=BaseVenda)
def cadastrar_venda(venda_data: BaseVenda):
    
    venda = Venda(
        user=venda_data.user,
        produtos=venda_data.produtos, 
        cupom_de_desconto=venda_data.cupom_de_desconto,
        pedido_personalizado=venda_data.pedido_personalizado
    )
    total = 0
    for produto in venda.produtos:
        total += produto.preco
        
    venda.total = total
    
    with Session(get_engine()) as session:
        session.add(venda)
        session.commit()
        session.refresh(venda)
        return venda
  
@router.patch("/{venda_id}")
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
        
        # Atualizar os campos fornecidos
        if venda_data.status:
            venda_to_update.status = venda_data.status
        
            
        # Salvar as alterações no banco de dados
        session.add(venda_to_update)
        session.commit()
        session.refresh(venda_to_update)

        return {"message": "Venda com sucesso!", "venda": venda_to_update}