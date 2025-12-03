from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.sql_models import Usuario, CargoEnum
from app.models.schemas import UsuarioCreate, UsuarioResponse
from app.security import get_current_user, get_password_hash

router = APIRouter(prefix="/members", tags=["Gestão de Acesso e Membros"])

@router.post("/", response_model=UsuarioResponse)
async def create_member(
    member: UsuarioCreate, 
    current_user: Usuario = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    # Regra de Negócio RN01: Apenas Presidente cadastra
    if current_user.cargo != CargoEnum.Presidente:
        raise HTTPException(status_code=403, detail="Apenas o Presidente pode cadastrar membros.")
    
    hashed_password = get_password_hash(member.senha)
    new_user = Usuario(
        nome=member.nome,
        email=member.email,
        senha_hash=hashed_password,
        cpf=member.cpf,
        telefone=member.telefone,
        cargo=member.cargo,
        departamento_id=member.departamento_id
    )
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao criar membro (Email/CPF duplicado?)")
    
    return new_user

@router.get("/", response_model=list[UsuarioResponse])
async def list_members(db: AsyncSession = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    result = await db.execute(select(Usuario))
    return result.scalars().all()