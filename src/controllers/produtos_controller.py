from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_admin, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
from src.database import get_engine
from src.models.admins_models import Admin
from src.models.categorias_models import Categoria
from src.models.produtos_models import BaseProduto, Produto, UpdateProdutoRequest

router = APIRouter()

@router.get("", response_model=List[Produto])
def listar_produtos():
    with Session(get_engine()) as session:
        statement = select(Produto)
        produtos = session.exec(statement).all()
        return produtos

@router.post("", response_model=BaseProduto)
def cadastrar_produto(produto_data: BaseProduto, admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        
        # Verifica dados do produto
        sttm = select(Produto).where(Produto.nome == produto_data.nome)
        produto = session.exec(sttm).first()
    
        if produto:
            raise HTTPException(status_code=400, detail='Produto já existe com esse nome!')
        if produto_data.preco<=0:
            raise HTTPException(status_code=400, detail='Preço invalido!')
        if produto_data.quantidade_estoque<=0:
            raise HTTPException(status_code=400, detail='Quantidade invalida!')
        
        # Verifica categoria
        sttm = select(Categoria).where(Categoria.id == produto_data.categoria)
        categoria = session.exec(sttm).first()
        
        if not categoria:
            raise HTTPException(status_code=400, detail='Categoria não existe!')
        
    produto = Produto(
        nome=produto_data.nome,
        preco=produto_data.preco, 
        foto=produto_data.foto,
        marca=produto_data.marca,
        categoria=produto_data.categoria,
        descricao=produto_data.descricao,
        quantidade_estoque=produto_data.quantidade_estoque,
        personalizado=produto_data.personalizado
    )
  
    with Session(get_engine()) as session:
        session.add(produto)
        session.commit()
        session.refresh(produto)
        return produto
  
@router.patch("/{produto_id}")
def atualizar_produto_por_id(
    produto_id: int,
    produto_data: UpdateProdutoRequest,
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        sttm = select(Produto).where(Produto.id == produto_id)
        produto_to_update = session.exec(sttm).first()

        if not produto_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado."
            )
        
        # Atualizar os campos fornecidos
        if produto_data.nome:
            produto_to_update.nome = produto_data.nome
        if produto_data.preco:
            produto_to_update.preco = produto_data.preco    
        if produto_data.foto:
            produto_to_update.foto = produto_data.foto    
        if produto_data.marca:
            produto_to_update.marca = produto_data.marca
        if produto_data.categoria:
            produto_to_update.categoria = produto_data.categoria
        if produto_data.descricao:
            produto_to_update.descricao = produto_data.descricao
        if produto_data.quantidade_estoque:
            produto_to_update.quantidade_estoque = produto_data.quantidade_estoque
        if produto_data.personalizado:
            produto_to_update.personalizado = produto_data.personalizado
        if produto_data.status:
            produto_to_update.status = produto_data.status
            
        # Salvar as alterações no banco de dados
        session.add(produto_to_update)
        session.commit()
        session.refresh(produto_to_update)

        return {"message": "Produto atualizado com sucesso!", "produto": produto_to_update}
    