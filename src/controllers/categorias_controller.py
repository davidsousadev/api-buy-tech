from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_admin, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
from src.database import get_engine
from src.models.admins_models import Admin
from src.models.categorias_models import BaseCategoria, Categoria

router = APIRouter()

@router.get("", response_model=List[Categoria])
def listar_categorias():
    with Session(get_engine()) as session:
        statement = select(Categoria)
        categorias = session.exec(statement).all()
        return categorias

@router.post("", response_model=BaseCategoria)
def cadastrar_categorias(categoria_data: BaseCategoria, admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        # Pega produto por nome
        sttm = select(Categoria).where(Categoria.name == categoria_data.name)
        categoria = session.exec(sttm).first()
    
    if categoria:
      raise HTTPException(status_code=400, detail='Categoria já existe com esse nome!')
    
    categoria = Categoria(
        name=categoria_data.name,
    )
  
    with Session(get_engine()) as session:
        session.add(categoria)
        session.commit()
        session.refresh(categoria)
        return categoria
  
@router.patch("/{categoria_id}")
def atualizar_categorias_por_id(
    categoria_id: int,
    categoria_data: BaseCategoria,
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        sttm = select(Categoria).where(Categoria.id == categoria_id)
        categoria_to_update = session.exec(sttm).first()

        if not categoria_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado."
            )
        
        # Atualizar os campos fornecidos
        if categoria_data.name:
            categoria_to_update.name = categoria_data.name
            
        # Salvar as alterações no banco de dados
        session.add(categoria_to_update)
        session.commit()
        session.refresh(categoria_to_update)

        return {"message": "Categoria atualizada com sucesso!", "Categorias": categoria_to_update}