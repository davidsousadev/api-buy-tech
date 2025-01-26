from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_admin, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
from src.database import get_engine
from src.models.admins_models import Admin
from src.models.categorias_models import BaseCategoria, Categoria

router = APIRouter()

# Lista os verbos disponiveis para esse controller
@router.options("", status_code=status.HTTP_200_OK)
async def options_categorias():
    return { "methods": ["GET", "POST", "PATCH"] }

# Listar categorias com filtragem opcional
@router.get("", response_model=List[Categoria])
def listar_categorias(
    id: int | None = None,
    nome: str | None = None
):
    with Session(get_engine()) as session:
        statement = select(Categoria)

        # Aplicar filtros dinamicamente
        if id is not None:
            statement = statement.where(Categoria.id == id)
        if nome:
            statement = statement.where(Categoria.nome.contains(nome))
        
        categorias = session.exec(statement).all()
        return categorias

# Cadastrar categorias
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
        sttm = select(Categoria).where(Categoria.nome == categoria_data.nome)
        categoria = session.exec(sttm).first()
    
    if categoria:
      raise HTTPException(status_code=400, detail='Categoria já existe com esse nome!')
    
    categoria = Categoria(
        nome=categoria_data.nome,
    )
  
    with Session(get_engine()) as session:
        session.add(categoria)
        session.commit()
        session.refresh(categoria)
        return categoria

# Atualizar categorias  
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
        # Verificar se a categoria com o ID fornecido existe
        sttm = select(Categoria).where(Categoria.id == categoria_id)
        categoria_to_update = session.exec(sttm).first()

        if not categoria_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoria não encontrada."
            )
            
        if categoria_to_update.nome == categoria_data.nome:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Não houve alteração de nome de categoria: {categoria_data.nome}"
            )
            
        # Verificar se já existe outra categoria com o mesmo nome
        sttm_nome = (
            select(Categoria)
            .where(Categoria.nome == categoria_data.nome, Categoria.id != categoria_id)
        )
        categoria_com_mesmo_nome = session.exec(sttm_nome).first()

        if categoria_com_mesmo_nome:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe outra categoria com o mesmo nome."
            )

        
        
        # Atualizar os campos fornecidos
        if categoria_data.nome:
            categoria_to_update.nome = categoria_data.nome

        # Salvar as alterações no banco de dados
        session.add(categoria_to_update)
        session.commit()
        session.refresh(categoria_to_update)

        return {
            "message": "Categoria atualizada com sucesso!",
            "categoria": categoria_to_update
        }
