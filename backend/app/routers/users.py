from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.sql_models import Usuario # Seu modelo do SQLAlchemy
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/users", tags=["Gestão de Usuários"])

# --- Schemas (Para não devolver a senha no JSON) ---
class UserResponse(BaseModel):
    id: int
    nome: str
    email: str
    cargo: str
    departamento_id: Optional[int] = None
    
    class Config:
        orm_mode = True # Permite ler direto do objeto do Banco SQL

class UserUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    cargo: Optional[str] = None
    # Adicione outros campos se necessário

# --- Rotas ---

@router.get("/", response_model=List[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    # Busca todos os usuários no banco SQL
    result = await db.execute(select(Usuario))
    users = result.scalars().all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    db: AsyncSession = Depends(get_db)
):
    # Busca o usuário
    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Atualiza apenas os campos enviados
    update_data_dict = user_data.dict(exclude_unset=True)
    for key, value in update_data_dict.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    await db.delete(user)
    await db.commit()
    return