from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, desc
from src.auth_utils import get_logged_admin
from src.database import get_engine
from sqlalchemy import func
from src.models.admins_models import Admin
from src.models.categorias_models import Categoria
from src.models.produtos_models import BaseProduto, Produto, UpdateProdutoRequest

router = APIRouter()

# Lista os verbos disponiveis para esse controller
@router.options("", status_code=status.HTTP_200_OK)
async def options_produtos():
    return { "methods": ["GET", "POST", "PATCH"] }

@router.get("", response_model=List[Produto])
def listar_produtos(
    id: int | None = None,
    nome: str | None = None,
    preco_min: float | None = None,
    preco_max: float | None = None,
    categoria: int | None = None,
    personalizado: bool | None = None,
    status: bool | None = None,
    quantidade_min: int | None = None,
    quantidade_max: int | None = None,
    criacao_inicio: str | None = None,
    criacao_fim: str | None = None,
    marca: str | None = None,
    descricao: str | None = None
):
    with Session(get_engine()) as session:
        statement_base = select(Produto)

        # Aplica filtros exceto nome
        if id is not None:
            statement_base = statement_base.where(Produto.id == id)
        if preco_min is not None:
            statement_base = statement_base.where(Produto.preco >= preco_min)
        if preco_max is not None:
            statement_base = statement_base.where(Produto.preco <= preco_max)
        if categoria is not None:
            statement_base = statement_base.where(Produto.categoria == categoria)
        if personalizado is not None:
            statement_base = statement_base.where(Produto.personalizado == personalizado)
        if status is not None:
            statement_base = statement_base.where(Produto.status == status)
        if quantidade_min is not None:
            statement_base = statement_base.where(Produto.quantidade_estoque >= quantidade_min)
        if quantidade_max is not None:
            statement_base = statement_base.where(Produto.quantidade_estoque <= quantidade_max)
        if criacao_inicio:
            statement_base = statement_base.where(Produto.criacao >= criacao_inicio)
        if criacao_fim:
            statement_base = statement_base.where(Produto.criacao <= criacao_fim)
        if marca:
            statement_base = statement_base.where(Produto.marca.contains(marca))
        if descricao:
            statement_base = statement_base.where(Produto.descricao.contains(descricao))

        statement_base = statement_base.order_by(desc(Produto.status))

        produtos = []

        if nome:
            tentativas = []

            if len(nome) == 1:
                tentativas.append(nome)
            elif len(nome) >= 3:
                tentativas.append(nome)     
                tentativas.append(nome[:3]) 
                tentativas.append(nome[-3:])
                tentativas.append(nome[:2]) 
                tentativas.append(nome[:1]) 
            else:
                for t in range(len(nome), 0, -1):
                    tentativas.append(nome[:t])
            produtos = []
            for fragmento in tentativas:
                if len(fragmento) == 1:
                    statement = statement_base.where(Produto.nome.ilike(f"{fragmento}%"))
                else:
                    statement = statement_base.where(Produto.nome.ilike(f"%{fragmento}%"))
                produtos = session.exec(statement).all()
                if produtos:
                    break

            if not produtos:
                primeira_letra = nome[0]
                statement = statement_base.where(Produto.nome.ilike(f"{primeira_letra}%"))
                produtos = session.exec(statement).all()

            if not produtos:
                primeiro_produto = session.exec(
                    select(Produto.nome).order_by(Produto.nome.asc()).limit(1)
                ).first()
                if primeiro_produto:
                    primeira_letra_produto = primeiro_produto[0][0]  # primeira letra do nome do produto
                    statement = statement_base.where(Produto.nome.ilike(f"{primeira_letra_produto}%"))
                    produtos = session.exec(statement).all()

        else:
            produtos = session.exec(statement_base).all()

        return produtos

# Busca um produto específico pelo ID
@router.get("/{id}", response_model=Produto)
def buscar_produto(id: int):
    with Session(get_engine()) as session:
        produto = session.get(Produto, id)
        if not produto:
            raise HTTPException(status_code=status.HTTP_200_OK, detail="Produto não encontrado")
        return produto

# Cadastra produtos
@router.post("", response_model=BaseProduto)
def cadastrar_produto(produto_data: BaseProduto, admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        
        # Verifica dados do produto
        sttm = select(Produto).where(Produto.nome == produto_data.nome)
        produto = session.exec(sttm).first()
    
        if produto:
            raise HTTPException(status_code=status.HTTP_200_OK, detail='Produto já existe com esse nome!')
        if produto_data.preco<=0:
            raise HTTPException(status_code=status.HTTP_200_OK, detail='Preço invalido!')
        if produto_data.quantidade_estoque<=0:
            raise HTTPException(status_code=status.HTTP_200_OK, detail='Quantidade invalida!')
        
        # Verifica categoria
        sttm = select(Categoria).where(Categoria.id == produto_data.categoria)
        categoria = session.exec(sttm).first()
        
        if not categoria:
            raise HTTPException(status_code=status.HTTP_200_OK, detail='Categoria não existe!')
        
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

# Cadastra produtos em massa
@router.post("/massa", response_model=List[BaseProduto])
def cadastrar_produtos_em_massa(
    produtos_data: List[BaseProduto],
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )
    
    produtos_cadastrados = []

    with Session(get_engine()) as session:
        for produto_data in produtos_data:

            # Verifica se o produto já existe
            sttm = select(Produto).where(Produto.nome == produto_data.nome)
            produto_existente = session.exec(sttm).first()

            if produto_existente:
                continue  # Pula produtos já cadastrados

            # Valida preço e quantidade
            if produto_data.preco <= 0 or produto_data.quantidade_estoque <= 0:
                continue  # Pula produtos inválidos

            # Verifica categoria
            sttm = select(Categoria).where(Categoria.id == produto_data.categoria)
            categoria = session.exec(sttm).first()

            if not categoria:
                continue  # Pula se a categoria não existe

            # Cria e adiciona o produto
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

            session.add(produto)
            session.commit()
            session.refresh(produto)

            produtos_cadastrados.append(produto)

    if not produtos_cadastrados:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Nenhum produto foi cadastrado. Verifique se já existem ou se os dados estão corretos."
        )

    return produtos_cadastrados

# Atualiza produtos por id  
@router.patch("/{produto_id}")
def atualizar_produto_por_id(
    produto_id: int,
    produto_data: UpdateProdutoRequest,
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        sttm = select(Produto).where(Produto.id == produto_id)
        produto_to_update = session.exec(sttm).first()

        if not produto_to_update:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
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
    