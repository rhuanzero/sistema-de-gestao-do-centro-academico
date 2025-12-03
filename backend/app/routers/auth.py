from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.sql_models import Usuario
from app.security import verify_password, create_access_token, get_password_hash
from app.models.schemas import Token

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Busca usuário
    result = await db.execute(select(Usuario).where(Usuario.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status.value == "Inativo":
        raise HTTPException(status_code=400, detail="Usuário inativo")

    access_token = create_access_token(data={"sub": user.email, "role": user.cargo.value})
    return {"access_token": access_token, "token_type": "bearer"}