from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_admin, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
from src.database import get_engine
from src.models.admins_models import Admin
from src.models.cupons_models import BaseCupom, Cupom

router = APIRouter()

@router.get("", response_model=List[Cupom])
def listar_cupons(admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem listar cupons."
        )
    with Session(get_engine()) as session:
        statement = select(Cupom)
        cupoms = session.exec(statement).all()
        return cupoms

@router.post("", response_model=BaseCupom)
def cadastrar_cupons(cupom_data: BaseCupom, admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        # Pega cupom por nome
        sttm = select(Cupom).where(Cupom.nome == cupom_data.nome)
        cupom = session.exec(sttm).first()
    
    if cupom:
      raise HTTPException(status_code=400, detail='Cupom já existe com esse nome!')
    if (1 <= cupom_data.valor <= 5000) and (5 <= len(cupom_data.nome) <= 20):
        cupom = Cupom(
            nome=cupom_data.nome,
            valor=cupom_data.valor,
            tipo=cupom_data.tipo
            )
    
        session.add(cupom)
        session.commit()
        session.refresh(cupom)
        return cupom
    else: 
        raise HTTPException(status_code=400, detail='Cupom invalido!')
    
@router.patch("/{cupom_id}")
def atualizar_cupons_por_id(
    cupom_id: int,
    cupom_data: BaseCupom,
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        sttm = select(Cupom).where(Cupom.id == cupom_id)
        cupom_to_update = session.exec(sttm).first()

        if not cupom_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cupom não encontrado."
            )
        if cupom_to_update.nome==cupom_data.nome:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cupom já existe."
            )
        if cupom_data.valor>100 and cupom_data.tipo==False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cupom de desconto não pode ser mais que 100%."
            ) 
               
        # Atualizar os campos fornecidos
        if cupom_data.nome:
            cupom_to_update.nome = cupom_data.nome
        if cupom_data.valor:
            cupom_to_update.valor = cupom_data.valor
        if cupom_data.tipo:
            cupom_to_update.tipo = cupom_data.tipo
        if cupom_data.tipo==False:
            cupom_to_update.tipo = cupom_data.tipo  
              
        # Salvar as alterações no banco de dados
        session.add(cupom_to_update)
        session.commit()
        session.refresh(cupom_to_update)

        return {"message": "Cupom atualizada com sucesso!", "cupoms": cupom_to_update}
    