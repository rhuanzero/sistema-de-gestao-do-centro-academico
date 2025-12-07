from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_
from app.database import get_db
from app.models.sql_models import (
    Transacao, Usuario, CargoEnum, TipoTransacao, 
    CentroAcademico
)
from app.models.schemas import TransacaoCreate, TransacaoResponse, TransacaoUpdate, BalanceResponse, ReportResponse
from app.security import get_current_user
from datetime import datetime, date as date_type
from typing import Union, List
from decimal import Decimal
import logging

# 👇 PREFIXO CORRIGIDO PARA /financeiro
router = APIRouter(prefix="/financeiro", tags=["Módulo Financeiro"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FUNÇÃO AUXILIAR ---
async def atualizar_saldo_ca(
    db: AsyncSession, 
    centro_academico_id: int, 
    valor: Decimal, 
    tipo: TipoTransacao
) -> None:
    if tipo == TipoTransacao.Receita:
        stmt = update(CentroAcademico).where(CentroAcademico.id == centro_academico_id).values(saldo=CentroAcademico.saldo + valor)
    else:
        stmt = update(CentroAcademico).where(CentroAcademico.id == centro_academico_id).values(saldo=CentroAcademico.saldo - valor)
    
    await db.execute(stmt)

# --- ROTAS ---

@router.get("/transactions", response_model=List[TransacaoResponse])
async def list_transactions(
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Lista transações do CA do usuário logado
    query = (
        select(Transacao)
        .where(Transacao.centro_academico_id == current_user.centro_academico_id)
        .order_by(Transacao.data.desc(), Transacao.id.desc())
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/transactions", response_model=TransacaoResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transacao: TransacaoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.cargo not in {CargoEnum.Tesoureiro, CargoEnum.Presidente}:
        raise HTTPException(status_code=403, detail="Acesso restrito.")

    # Compatibilidade Pydantic v1/v2
    try:
        dados_transacao = transacao.model_dump(exclude={"usuario_id", "centro_academico_id"})
    except AttributeError:
        dados_transacao = transacao.dict(exclude={"usuario_id", "centro_academico_id"})

    try:
        nova_transacao = Transacao(
            **dados_transacao,
            usuario_id=current_user.id,
            centro_academico_id=current_user.centro_academico_id
        )
        
        db.add(nova_transacao)
        
        # Atualiza Saldo
        await atualizar_saldo_ca(
            db=db,
            centro_academico_id=current_user.centro_academico_id,
            valor=transacao.valor,
            tipo=transacao.tipo
        )
        
        await db.commit()
        await db.refresh(nova_transacao)
        return nova_transacao
        
    except Exception as e:
        logger.error(f"Erro: {repr(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao processar transação.")

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    current_user: Usuario = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    ca = await db.get(CentroAcademico, current_user.centro_academico_id)
    if not ca:
        raise HTTPException(status_code=404, detail="CA não encontrado.")
    
    # Cálculos de totais
    receitas = await db.execute(select(func.sum(Transacao.valor)).where(and_(
            Transacao.centro_academico_id == current_user.centro_academico_id,
            Transacao.tipo == TipoTransacao.Receita
        )))
    
    despesas = await db.execute(select(func.sum(Transacao.valor)).where(and_(
            Transacao.centro_academico_id == current_user.centro_academico_id,
            Transacao.tipo == TipoTransacao.Despesa
        )))
    
    total_receitas = receitas.scalar() or Decimal('0')
    total_despesas = despesas.scalar() or Decimal('0')
    
    return {
        "saldo_atual": float(ca.saldo),
        "receitas": float(total_receitas),
        "despesas": float(total_despesas),
        "ultima_atualizacao": datetime.now().isoformat()
    }

# ... (Mantenha as rotas de report, put e delete que você já tinha)