from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_admin
from src.database import get_engine
from src.models.admins_models import Admin
from src.models.cupons_models import BaseCupom, Cupom

router = APIRouter()

from fastapi import Query

# Lista os verbos disponiveis para esse controller
@router.options("", status_code=status.HTTP_200_OK)
async def options_revendedores():
    return { "methods": ["GET", "POST", "PATCH"] }


# Clientes Verificar Cupons
@router.get("/verificar-cupom")
def verificar_cupons( cupom_nome: str):

    with Session(get_engine()) as session:
        # Base da consulta
        statement = select(Cupom).where(Cupom.nome==cupom_nome)
        cupom = session.exec(statement).first()
        if cupom:
            if cupom.quantidade_de_ultilizacao == 0:
                    raise HTTPException(
                        status_code=status.HTTP_204_NO_CONTENT,
                        detail="A quantidade máxima de cupons já foi resgatada."
                    )
            else:
                return {
                    "cupom": cupom
                    }
        else:
            return {
                "cupom": False
                }

# Adminitradores Listar Cupons
@router.get("/admin", response_model=List[Cupom])
def listar_cupons(
    admin: Annotated[Admin, Depends(get_logged_admin)],
    nome: str | None = None,
    valor_min: float | None = None,
    valor_max: float | None = None,
    tipo: bool | None = None,
    resgatado: bool | None = None
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado! Apenas administradores podem listar cupons."
        )

    with Session(get_engine()) as session:
        # Base da consulta
        statement = select(Cupom)

        # Filtros dinâmicos
        if nome:
            statement = statement.where(Cupom.nome.ilike(f"%{nome}%"))
        if valor_min is not None:
            statement = statement.where(Cupom.valor >= valor_min)
        if valor_max is not None:
            statement = statement.where(Cupom.valor <= valor_max)
        if tipo is not None:
            statement = statement.where(Cupom.tipo == tipo)
        if resgatado is not None:
            statement = statement.where(Cupom.resgatado == resgatado)

        # Executa a consulta
        cupons = session.exec(statement).all()
        return cupons

# Adminitradores Listar Cupons por id
@router.get("/admin/{cupom_id}")
def listar_cupons(
    admin: Annotated[Admin, Depends(get_logged_admin)],
    cupom_id: int
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado! Apenas administradores podem listar cupons."
        )

    with Session(get_engine()) as session:
        # Base da consulta
        statement = select(Cupom).where(Cupom.id==cupom_id)

        # Executa a consulta
        cupom = session.exec(statement).first()
        if cupom:
            return cupom
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Cupom não localizado."
        )

# Administradores Cadastrar cupons
@router.post("", response_model=BaseCupom)
def cadastrar_cupons(cupom_data: BaseCupom, admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if cupom_data.valor>100 and cupom_data.tipo==False:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Cupom de desconto não pode ser mais que 100%."
            )
    
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        # Pega cupom por nome
        sttm = select(Cupom).where(Cupom.nome == cupom_data.nome)
        cupom = session.exec(sttm).first()
    
    if cupom:
        raise HTTPException(status_code=status.HTTP_200_OK, detail='Cupom já existe com esse nome!')
    
    
    
    if (1 <= cupom_data.valor <= 5000) and (5 <= len(cupom_data.nome) <= 20):
        cupom = Cupom(
            nome=cupom_data.nome,
            valor=cupom_data.valor,
            tipo=cupom_data.tipo,
            quantidade_de_ultilizacao=cupom_data.quantidade_de_ultilizacao
            )
    
        session.add(cupom)
        session.commit()
        session.refresh(cupom)
        return cupom
    else: 
        raise HTTPException(status_code=status.HTTP_200_OK00, detail='Cupom invalido!')
 
# Administradores Atualizar cupons   
@router.patch("/{cupom_id}")
def atualizar_cupons_por_id(
    cupom_id: int,
    cupom_data: BaseCupom,
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Acesso negado!"
        )
    
    if cupom_data.valor > 100 and cupom_data.tipo == False:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Cupom de desconto não pode ser mais que 100%."
        ) 

    with Session(get_engine()) as session:
        # Busca o cupom para atualizar
        sttm = select(Cupom).where(Cupom.id == cupom_id)
        cupom_to_update = session.exec(sttm).first()

        if not cupom_to_update:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Cupom não encontrado."
            )
        
        # Verifica se há outro cupom com o mesmo nome, excluindo o cupom que está sendo atualizado
        cupom_existente = session.exec(select(Cupom).where(Cupom.nome == cupom_data.nome)).first()

        # Se encontrar um cupom com o mesmo nome e for diferente do cupom atual, lança um erro
        if cupom_existente and cupom_existente.id != cupom_id:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Cupom já existe."
            )
        
        # Verificação de cupons resgatados
        if cupom_to_update.resgatado == True:
            if cupom_data.nome != cupom_to_update.nome and cupom_data.valor != cupom_to_update.valor and cupom_data.tipo != cupom_to_update.tipo:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail="Cupom já resgatado não pode ter dados atualizado."
                )

        # Se o cupom não foi resgatado, permite atualização do nome
        if cupom_to_update.resgatado == False:
            if cupom_data.nome:
                cupom_to_update.nome = cupom_data.nome
        
        # Atualizar os outros campos do cupom
        if cupom_data.valor:
            cupom_to_update.valor = cupom_data.valor
        if cupom_data.tipo:
            cupom_to_update.tipo = cupom_data.tipo
        if cupom_data.tipo == False:
            cupom_to_update.tipo = cupom_data.tipo 
        if cupom_data.quantidade_de_ultilizacao:
            cupom_to_update.quantidade_de_ultilizacao = cupom_data.quantidade_de_ultilizacao

        # Salvar as alterações no banco de dados
        session.add(cupom_to_update)
        session.commit()
        session.refresh(cupom_to_update)

        return {"message": "Cupom atualizado com sucesso!", "cupom": cupom_to_update}
