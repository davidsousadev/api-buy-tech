from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_admin, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
from src.database import get_engine
from src.models.admins_models import Admin
from src.models.products_models import BaseProduct, Product, UpdateProductRequest

router = APIRouter()

@router.get("", response_model=List[Product])
def listar_produtos():
    with Session(get_engine()) as session:
        statement = select(Product)
        products = session.exec(statement).all()
        return products

@router.post("", response_model=BaseProduct)
def cadastrar_produto(product_data: BaseProduct, admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        # Pega produto por nome
        sttm = select(Product).where(Product.name == product_data.name)
        product = session.exec(sttm).first()
    
    if product:
      raise HTTPException(status_code=400, detail='Produto já existe com esse nome!')
    
    product = Product(
        name=product_data.name,
        preco=product_data.preco, 
        foto=product_data.foto,
        marca=product_data.marca,
        categoria=product_data.categoria,
        descricao=product_data.descricao,
        quantidade_estoque=product_data.quantidade_estoque,
        personalizado=product_data.personalizado
    )
  
    with Session(get_engine()) as session:
        session.add(product)
        session.commit()
        session.refresh(product)
        return product
  
@router.patch("/{product_id}")
def atualizar_produto_por_id(
    product_id: int,
    product_data: UpdateProductRequest,
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        sttm = select(Product).where(Product.id == product_id)
        product_to_update = session.exec(sttm).first()

        if not product_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado."
            )
        
        # Atualizar os campos fornecidos
        if product_data.name:
            product_to_update.name = product_data.name
        if product_data.preco:
            product_to_update.preco = product_data.preco    
        if product_data.foto:
            product_to_update.foto = product_data.foto    
        if product_data.marca:
            product_to_update.marca = product_data.marca
        if product_data.categoria:
            product_to_update.categoria = product_data.categoria
        if product_data.descricao:
            product_to_update.descricao = product_data.descricao
        if product_data.quantidade_estoque:
            product_to_update.quantidade_estoque = product_data.quantidade_estoque
        if product_data.personalizado:
            product_to_update.personalizado = product_data.personalizado
        if product_data.status:
            product_to_update.status = product_data.status
            
        # Salvar as alterações no banco de dados
        session.add(product_to_update)
        session.commit()
        session.refresh(product_to_update)

        return {"message": "Produto atualizado com sucesso!", "product": product_to_update}