from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

# Ajuste os imports conforme a estrutura das suas pastas
from app.database import get_db
from app.models.sql_models import Usuario, CentroAcademico, StatusEnum, CargoEnum
from app.security import (
    verify_password, 
    create_access_token, 
    get_password_hash, 
    get_current_user, # Usado apenas no /me agora
    oauth2_scheme,
    pwd_context
)
from app.models.schemas import Token, UsuarioCreate, UsuarioResponse
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# --- ROTA DE LOGIN ---
@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """
    Autentica um usuário e retorna um token JWT.
    """
    # Busca usuário por email ou CPF
    result = await db.execute(
        select(Usuario)
        .where(
            or_(
                Usuario.email == form_data.username,
                Usuario.cpf == form_data.username
            )
        )
    )
    user = result.scalars().first()
    
    # Verifica senha
    if not user or not verify_password(form_data.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email/CPF ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verifica Status
    if user.status == StatusEnum.Inativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo. Contate o administrador."
        )

    # Verifica se o Centro Acadêmico do usuário está ativo (se ele tiver um)
    if user.centro_academico_id:
        ca = await db.get(CentroAcademico, user.centro_academico_id)
        if not ca:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Centro Acadêmico não encontrado."
            )

    # Cria o token de acesso
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )
    
    # Retorna o token e dados básicos
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": user.id,
        "cargo": user.cargo.value if user.cargo else None,
        "centro_academico_id": user.centro_academico_id
    }

# --- ROTA DE REGISTRO (AGORA PÚBLICA) ---
@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UsuarioCreate,
    db: AsyncSession = Depends(get_db)
    # REMOVIDO: current_user: Usuario = Depends(get_current_user)
    # Motivo: Permitir cadastro inicial sem login
):
    """
    Registra um novo usuário.
    Rota pública para permitir o cadastro inicial (ex: Presidente).
    """
    
    # Verifica se o email já está em uso
    result = await db.execute(select(Usuario).where(Usuario.email == user_data.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso"
        )
    
    # Verifica se o CPF já está em uso (se fornecido)
    if user_data.cpf:
        result = await db.execute(select(Usuario).where(Usuario.cpf == user_data.cpf))
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF já está em uso"
            )
    
    # Cria o hash da senha
    hashed_password = get_password_hash(user_data.senha)
    
    # Prepara os dados para salvar
    # .dict() é usado no Pydantic v1. Se usar v2, prefira .model_dump()
    user_dict = user_data.dict(exclude={"senha"}) 
    user_dict["senha_hash"] = hashed_password
    
    # (Opcional) Se quiser forçar o primeiro usuário como Presidente, pode fazer logica aqui.
    # Mas vamos confiar no que veio do front por enquanto.

    db_user = Usuario(**user_dict)
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user

# --- ROTA ME (PERFIL) ---
@router.get("/me", response_model=UsuarioResponse)
async def read_users_me(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna os dados do usuário autenticado.
    """
    # Carrega as relações necessárias (ex: departamento) se precisar
    # Se der erro de lazy loading, descomente as linhas abaixo:
    # result = await db.execute(
    #     select(Usuario)
    #     .where(Usuario.id == current_user.id)
    #     .options(selectinload(Usuario.departamento))
    # )
    # user = result.scalars().first()
    # return user
    
    return current_user