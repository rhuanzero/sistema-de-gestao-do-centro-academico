from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.sql_models import Usuario, CargoEnum
from app.models.schemas import UsuarioCreate, UsuarioResponse, UsuarioUpdate
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
    query = select(Usuario)

    if current_user.cargo == CargoEnum.Coordenador:
        if not current_user.departamento_id:
            raise HTTPException(status_code=400, detail="Coordenador não está associado a um departamento.")
        query = query.where(Usuario.departamento_id == current_user.departamento_id)
    
    elif current_user.cargo != CargoEnum.Presidente:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    result = await db.execute(query)
    return result.scalars().all()

@router.put("/{member_id}", response_model=UsuarioResponse)
async def update_member(
    member_id: int,
    member_update: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.cargo != CargoEnum.Presidente:
        raise HTTPException(status_code=403, detail="Apenas o Presidente pode modificar membros.")

    result = await db.execute(select(Usuario).where(Usuario.id == member_id))
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    update_data = member_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "senha":
            if value:
                setattr(db_user, "senha_hash", get_password_hash(value))
        else:
            setattr(db_user, key, value)

    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar usuário: {e}")

    return db_user