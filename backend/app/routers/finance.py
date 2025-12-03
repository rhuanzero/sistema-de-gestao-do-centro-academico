from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.sql_models import Transacao, Usuario, CargoEnum, TipoTransacao
from app.models.schemas import TransacaoCreate, TransacaoResponse
from app.security import get_current_user
from datetime import date

router = APIRouter(prefix="/finance", tags=["Módulo Financeiro"])

@router.post("/transactions", response_model=TransacaoResponse)
async def create_transaction(
    transacao: TransacaoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Regra de Negócio RN07: Apenas Tesoureiro registra
    if current_user.cargo != CargoEnum.Tesoureiro:
        raise HTTPException(status_code=403, detail="Apenas o Tesoureiro pode registrar transações.")

    new_transacao = Transacao(
        **transacao.model_dump(),
        usuario_id=current_user.id
    )
    db.add(new_transacao)
    await db.commit()
    await db.refresh(new_transacao)
    return new_transacao

@router.get("/balance") # UC06
async def get_balance(current_user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.cargo not in [CargoEnum.Presidente, CargoEnum.Tesoureiro]:
         raise HTTPException(status_code=403, detail="Acesso negado.")

    receitas = await db.execute(select(func.sum(Transacao.valor)).where(Transacao.tipo == TipoTransacao.Receita))
    despesas = await db.execute(select(func.sum(Transacao.valor)).where(Transacao.tipo == TipoTransacao.Despesa))
    
    total_receitas = receitas.scalar() or 0
    total_despesas = despesas.scalar() or 0
    
    return {
        "receitas": total_receitas,
        "despesas": total_despesas,
        "saldo": total_receitas - total_despesas
    }

@router.get("/report") # UC03
async def generate_report(start_date: date, end_date: date, db: AsyncSession = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.cargo != CargoEnum.Tesoureiro:
         raise HTTPException(status_code=403, detail="Apenas tesoureiro gera relatórios.")
    
    query = select(Transacao).where(
        Transacao.data_transacao >= start_date,
        Transacao.data_transacao <= end_date
    )
    result = await db.execute(query)
    transacoes = result.scalars().all()
    
    return {"periodo": f"{start_date} a {end_date}", "dados": transacoes}