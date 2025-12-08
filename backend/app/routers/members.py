from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.database import get_db
from app.models.sql_models import Usuario, CargoEnum
from app.models.schemas import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.security import get_current_user, get_password_hash

router = APIRouter(prefix="/membros", tags=["Gestão de Acesso e Membros"])

# --- CRIAR MEMBRO ---
@router.post("/", response_model=UsuarioResponse)
async def create_member(
    member: UsuarioCreate, 
    current_user: Usuario = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    # Regra 1: Apenas Presidente
    if current_user.cargo != CargoEnum.Presidente:
        raise HTTPException(status_code=403, detail="Apenas o Presidente pode cadastrar membros.")
    
    hashed_password = get_password_hash(member.senha)
    
    # Regra 2: O novo membro nasce AUTOMATICAMENTE no CA do Presidente logado
    new_user = Usuario(
        nome=member.nome,
        email=member.email,
        senha_hash=hashed_password,
        cpf=member.cpf,
        telefone=member.telefone,
        cargo=member.cargo,
        departamento_id=member.departamento_id,
        centro_academico_id=current_user.centro_academico_id # <--- Trava de segurança
    )
    
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
    except Exception as e:
        await db.rollback()
        # Log do erro real no terminal para você debugar se precisar
        print(f"Erro ao criar membro: {e}")
        raise HTTPException(status_code=400, detail="Erro ao criar membro. Verifique se Email ou CPF já existem.")
    
    return new_user

# --- LISTAR MEMBROS ---
# Substitua o list_members por isso TEMPORARIAMENTE para testar
@router.get("/", response_model=list[UsuarioResponse])
async def list_members(
    db: AsyncSession = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    print(f"Buscando membros para o CA ID: {current_user.centro_academico_id}")

    # Query mais simples possível: Traga todos desse CA
    query = select(Usuario).where(Usuario.centro_academico_id == current_user.centro_academico_id)
    
    result = await db.execute(query)
    membros = result.scalars().all()
    
    print(f"Encontrados: {len(membros)} membros.")
    return membros

# --- ATUALIZAR MEMBRO ---
@router.put("/{member_id}", response_model=UsuarioResponse)
async def update_member(
    member_id: int,
    member_update: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.cargo != CargoEnum.Presidente:
        raise HTTPException(status_code=403, detail="Apenas o Presidente pode modificar membros.")

    # Busca usuário
    result = await db.execute(select(Usuario).where(Usuario.id == member_id))
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # SEGURANÇA EXTRA: Verifica se o usuário alvo é do mesmo CA
    if db_user.centro_academico_id != current_user.centro_academico_id:
        raise HTTPException(status_code=403, detail="Você não pode alterar membros de outro CA.")

    # Atualiza dados
    update_data = member_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "senha":
            if value: # Só atualiza senha se vier alguma coisa
                setattr(db_user, "senha_hash", get_password_hash(value))
        else:
            setattr(db_user, key, value)

    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar: {str(e)}")

    return db_user

# --- DELETAR MEMBRO ---
@router.delete("/{member_id}", status_code=204)
async def delete_member(
    member_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    # 1. Verifica permissão
    if current_user.cargo != CargoEnum.Presidente:
        raise HTTPException(status_code=403, detail="Apenas o Presidente pode excluir membros.")

    # 2. Busca o usuário
    query = select(Usuario).where(Usuario.id == member_id)
    result = await db.execute(query)
    member_to_delete = result.scalars().first()

    # 3. Validações
    if not member_to_delete:
        raise HTTPException(status_code=404, detail="Membro não encontrado.")

    # SEGURANÇA EXTRA: Verifica se é do mesmo CA
    if member_to_delete.centro_academico_id != current_user.centro_academico_id:
        raise HTTPException(status_code=403, detail="Você não pode excluir membros de outro CA.")

    # 4. Proteção contra auto-exclusão
    if member_to_delete.id == current_user.id:
        raise HTTPException(status_code=400, detail="Você não pode excluir sua própria conta.")

    # 5. Deleta
    await db.delete(member_to_delete)
    await db.commit()
    
    return None