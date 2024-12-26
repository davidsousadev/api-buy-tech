from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.auth_utils import get_logged_user, get_logged_admin, hash_password, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
from src.database import get_engine
from src.models.admin_models import BaseAdmin, SignInAdminRequest, SignUpAdminRequest, Admin, AdminResponse, UpdateAdminRequest
from src.models.user_models import User,  UpdateUserRequest, UserResponse, BaseUser, SignUpUserRequest
from passlib.context import CryptContext
import jwt

router = APIRouter()
            
@router.post('/cadastrar', response_model=BaseAdmin)
def cadastrar_admins(admin_data: SignUpAdminRequest, ref: int | None = None):
    with Session(get_engine()) as session:
        sttm = select(Admin).where(Admin.email == admin_data.email)
        admin = session.exec(sttm).first()

        if admin:
            raise HTTPException(status_code=400, detail='Já existe um usuário com esse email')

    if admin_data.password != admin_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Senhas não coincidem!'
        )

    # Hash da senha
    hash = hash_password(admin_data.password)
    link = 0
    if ref != None:
      link = ref
      
    admin = Admin(
            name=admin_data.name,
            email=admin_data.email, 
            password=hash,
            cpf=admin_data.cpf,
            data_nascimento=admin_data.data_nascimento,
            telefone=admin_data.telefone,
            cep=admin_data.cep,
            pontos_fidelidade=0,
            clube_fidelidade=False,
            cod_indicacao=link,
            status=True,
            admin=True
            )

    with Session(get_engine()) as session:
        session.add(admin)
        session.commit()
        session.refresh(admin)
        return admin

@router.post('/logar')
def logar_admins(signin_data: SignInAdminRequest):
  with Session(get_engine()) as session:
    # pegar usuário por email
    
    sttm = select(Admin).where(Admin.email == signin_data.email)
    admin = session.exec(sttm).first()
    
    if not admin: # não encontrou usuário
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Usuário e/ou senha incorreto(S)')
    
    # encontrou, então verificar a senha
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    is_correct = pwd_context.verify(signin_data.password, admin.password)

    if not is_correct:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail='Usuário e/ou senha incorrento(S)')
    
    # Tá tudo OK pode gerar um Token JWT e devolver
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRES)
    access_token = jwt.encode({'sub': admin.email, 'exp': expires_at}, key=SECRET_KEY, algorithm=ALGORITHM)

    expires_rt = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_EXPIRES)
    refresh_token = jwt.encode({'sub': admin.email, 'exp': expires_rt}, key=SECRET_KEY, algorithm=ALGORITHM)


    return {'access_token': access_token, 'refresh_token': refresh_token}

@router.get('/autenticar', response_model=Admin)
def autenticar_admins(admin: Annotated[Admin, Depends(get_logged_admin)]):
  return admin

@router.patch("/atualizar/{admin_id}")
def atualizar_adiministrador(
    admin_id: int,
    admin_data: UpdateAdminRequest,
    admin: Annotated[Admin, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem atualizar admins."
        )
    with Session(get_engine()) as session:
        sttm = select(Admin).where(Admin.id == admin_id)
        admin_to_update = session.exec(sttm).first()

        if not admin_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )
        
        # Atualizar os campos fornecidos
        if admin_data.name:
            admin_to_update.name = admin_data.name
        if admin_data.email:
            admin_to_update.email = admin_data.email
        if admin_data.cpf:
            admin_to_update.cpf = admin_data.cpf
        if admin_data.data_nascimento:
            admin_to_update.data_nascimento = admin_data.data_nascimento
        if admin_data.telefone:
            admin_to_update.telefone = admin_data.telefone
        if admin_data.cep:
            admin_to_update.cep = admin_data.cep
        if admin_data.password:
            admin_to_update.password = hash_password(admin_data.password)
            
        # Salvar as alterações no banco de dados
        session.add(admin_to_update)
        session.commit()
        session.refresh(admin_to_update)

        return {"message": "Usuário atualizado com sucesso!", "user": admin_to_update}

@router.get("", response_model=list[AdminResponse])
def listar_admins(admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem listar admins."
        )

    with Session(get_engine()) as session:
        statement = select(Admin)
        admins = session.exec(statement).all()
        return [AdminResponse.model_validate(u) for u in admins]

@router.patch("/desativar/{admin_id}")
def desativar_admins(admin_id: int, admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem desativar administradores."
        )

    with Session(get_engine()) as session:
        sttm = select(Admin).where(Admin.id == admin_id)
        admin_to_update = session.exec(sttm).first()

        if not admin_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Administrador não encontrado."
            )

        admin_to_update.status = False
        session.add(admin_to_update)
        session.commit()
        session.refresh(admin_to_update)

        return {"message": "Administrador desativado com sucesso!"}

@router.post('/usuarios/cadastrar', response_model=BaseUser)
def cadastrar_usuarios(user_data: SignUpUserRequest, admin: Annotated[Admin, Depends(get_logged_admin)], ref: int | None = None):
    
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
      # pegar usuário por email
      sttm = select(User).where(User.email == user_data.email)
      user = session.exec(sttm).first()

      if user:
        raise HTTPException(status_code=400, detail='Já existe um usuário com esse email')

    if user_data.password != user_data.confirm_password:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail='Senhas não coincidem!')
    
    # Hash da senha
    hash = hash_password(user_data.password)
    link = 0
    if ref != None:
      link = ref

    user = User(
      name=user_data.name,
      email=user_data.email, 
      password=hash,
      cpf=user_data.cpf,
      data_nascimento=user_data.data_nascimento,
      telefone=user_data.telefone,
      cep=user_data.cep,
      pontos_fidelidade=0,
      clube_fidelidade=False,
      cod_indicacao=link,
      status=True
      )
    
    with Session(get_engine()) as session:
      session.add(user)
      session.commit()
      session.refresh(user)
      return user

@router.get("/usuarios", response_model=list[UserResponse])
def listar_usuarios(admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem listar usuarios."
        )

    with Session(get_engine()) as session:
        statement = select(User)
        users = session.exec(statement).all()
        return [UserResponse.model_validate(u) for u in users]

@router.patch("/usuarios/atualizar/{user_id}")
def atualizar_usuarios(
    user_id: int,
    user_data: UpdateUserRequest,
    admin: Annotated[User, Depends(get_logged_admin)],
):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        sttm = select(User).where(User.id == user_id)
        user_to_update = session.exec(sttm).first()

        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )
        
        # Atualizar os campos fornecidos
        if user_data.name:
            user_to_update.name = user_data.name
        if user_data.email:
            user_to_update.email = user_data.email
        if user_data.cpf:
            user_to_update.cpf = user_data.cpf
        if user_data.data_nascimento:
            user_to_update.data_nascimento = user_data.data_nascimento
        if user_data.telefone:
            user_to_update.telefone = user_data.telefone
        if user_data.cep:
            user_to_update.cep = user_data.cep
        if user_data.password:
            user_to_update.password = hash_password(user_data.password)
            
        # Salvar as alterações no banco de dados
        session.add(user_to_update)
        session.commit()
        session.refresh(user_to_update)

        return {"message": "Usuário atualizado com sucesso!", "user": user_to_update}

@router.patch("/usuarios/desativar/{user_id}")
def desativar_ususarios(user_id: int, admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado! Apenas administradores podem desativar usuários."
        )

    with Session(get_engine()) as session:
        sttm = select(User).where(User.id == user_id)
        user_to_update = session.exec(sttm).first()

        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )

        user_to_update.status = False
        session.add(user_to_update)
        session.commit()
        session.refresh(user_to_update)

        return {"message": "Usuário desativado com sucesso!"}