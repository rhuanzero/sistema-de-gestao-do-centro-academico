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
from datetime import datetime, timedelta, date as date_type
from typing import Union
from decimal import Decimal
import logging


router = APIRouter(prefix="/finance", tags=["Módulo Financeiro"])

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def atualizar_saldo_ca(
    db: AsyncSession, 
    centro_academico_id: int, 
    valor: Decimal, 
    tipo: TipoTransacao
) -> None:
    """
    Atualiza o saldo do Centro Acadêmico de forma atômica.
    """
    if tipo == TipoTransacao.Receita:
        stmt = (
            update(CentroAcademico)
            .where(CentroAcademico.id == centro_academico_id)
            .values(saldo=CentroAcademico.saldo + valor)
        )
    else:  # Despesa
        stmt = (
            update(CentroAcademico)
            .where(CentroAcademico.id == centro_academico_id)
            .values(saldo=CentroAcademico.saldo - valor)
        )
    
    await db.execute(stmt)
    await db.commit()

@router.post("/transactions", response_model=TransacaoResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transacao: TransacaoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Fail Fast: Verificação de permissão usando Set (mais performático que List)
    if current_user.cargo not in {CargoEnum.Tesoureiro, CargoEnum.Presidente}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito à Tesouraria ou Presidência."
        )

    # 2. Sanitização: Garante que IDs venham do token, não do corpo da requisição
    # Resolve o erro de "multiple values for keyword argument"
    dados_transacao = transacao.model_dump(exclude={"usuario_id", "centro_academico_id"})

    try:
        # 3. Criação do Objeto
        nova_transacao = Transacao(
            **dados_transacao,
            usuario_id=current_user.id,
            centro_academico_id=current_user.centro_academico_id
        )
        
        db.add(nova_transacao)
        
        # 4. Atualização de Saldo
        # Nota: Assume-se que 'transacao.valor' já é Decimal no Pydantic
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
        logger.error(f"Erro processando transação: {repr(e)}") # Log mais detalhado com repr()
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao processar a transação financeira."
        )

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    current_user: Usuario = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna o saldo atual do Centro Acadêmico.
    Apenas Presidente e Tesoureiro podem acessar.
    """
    if current_user.cargo not in [CargoEnum.Presidente, CargoEnum.Tesoureiro]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas Presidente e Tesoureiro podem acessar."
        )
    
    ca = await db.get(CentroAcademico, current_user.centro_academico_id)
    if not ca:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Centro Acadêmico não encontrado."
        )
    
    receitas = await db.execute(
        select(func.sum(Transacao.valor))
        .where(and_(
            Transacao.centro_academico_id == current_user.centro_academico_id,
            Transacao.tipo == TipoTransacao.Receita
        ))
    )
    
    despesas = await db.execute(
        select(func.sum(Transacao.valor))
        .where(and_(
            Transacao.centro_academico_id == current_user.centro_academico_id,
            Transacao.tipo == TipoTransacao.Despesa
        ))
    )
    
    total_receitas = receitas.scalar() or Decimal('0')
    total_despesas = despesas.scalar() or Decimal('0')
    saldo_calculado = total_receitas - total_despesas
    
    if abs(float(ca.saldo - saldo_calculado)) > 0.01:
        logger.warning(
            f"Inconsistência de saldo detectada para CA {ca.id}. "
            f"Saldo armazenado: {ca.saldo}, Saldo calculado: {saldo_calculado}"
        )
    
    return {
        "saldo_atual": float(ca.saldo),
        "receitas": float(total_receitas),
        "despesas": float(total_despesas),
        "ultima_atualizacao": datetime.now().isoformat()
    }


@router.get("/report", response_model=ReportResponse)
async def generate_report(
    start_date: Union[datetime, date_type] = date_type(1990, 1, 1), 
    end_date: Union[datetime, date_type] = date_type.today(),
    current_user: Usuario = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """
    Gera um relatório financeiro para o período especificado.
    Retorna todas as transações entre as datas fornecidas.
    Aceita tanto datas (YYYY-MM-DD) quanto datetimes completos (YYYY-MM-DDTHH:MM:SS).
    """
    # Converte date para datetime se necessário e ajusta para o início e fim do dia
    if isinstance(start_date, date_type):
        start_of_day = datetime.combine(start_date, datetime.min.time())
    else:
        start_of_day = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
    if isinstance(end_date, date_type):
        end_of_day = datetime.combine(end_date, datetime.max.time())
    else:
        end_of_day = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
    # Busca as transações no período
    result = await db.execute(
        select(Transacao, Usuario.nome.label("usuario_nome"))
        .join(Usuario, Transacao.usuario_id == Usuario.id)
        .where(
            Transacao.centro_academico_id == current_user.centro_academico_id,
            Transacao.data >= start_of_day,
            Transacao.data <= end_of_day
        )
        .order_by(Transacao.data.desc(), Transacao.id.desc())
    )
    
    transacoes = result.all()
    
    # Calcula totais
    totais = {"receitas": Decimal('0'), "despesas": Decimal('0')}
    
    # Formata os resultados
    dados_formatados = []
    for transacao in transacoes:
        valor = transacao.Transacao.valor
        if transacao.Transacao.tipo == TipoTransacao.Receita:
            totais["receitas"] += valor
        else:
            totais["despesas"] += valor
            
        dados_formatados.append({
            "id": transacao.Transacao.id,
            "data": transacao.Transacao.data.isoformat(),
            "descricao": transacao.Transacao.descricao,
            "valor": float(valor),
            "tipo": transacao.Transacao.tipo.value,
            "responsavel": transacao.usuario_nome
        })
    
    return {
        "periodo": {
            "inicio": start_date.isoformat(), 
            "fim": end_date.isoformat()
        },
        "total_receitas": float(totais["receitas"]),
        "total_despesas": float(totais["despesas"]),
        "saldo_periodo": float(totais["receitas"] - totais["despesas"]),
        "transacoes": dados_formatados,
        "total_registros": len(dados_formatados),
        "gerado_em": datetime.now().isoformat()
    }


@router.put("/transactions/{transaction_id}", response_model=TransacaoResponse)
async def update_transaction(
    transaction_id: int,
    transacao_update: TransacaoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Apenas Tesoureiro ou Presidente podem alterar transações
    if current_user.cargo not in {CargoEnum.Tesoureiro, CargoEnum.Presidente}:
        raise HTTPException(status_code=403, detail="Acesso restrito à Tesouraria ou Presidência.")

    result = await db.execute(select(Transacao).where(Transacao.id == transaction_id))
    tx = result.scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transação não encontrada.")

    # Calcular reversão do efeito anterior no saldo
    try:
        # Reverte o efeito da transação antiga
        reverse_type = TipoTransacao.Despesa if tx.tipo == TipoTransacao.Receita else TipoTransacao.Receita
        await atualizar_saldo_ca(db=db, centro_academico_id=tx.centro_academico_id, valor=tx.valor, tipo=reverse_type)

        # Aplica nova transação (se fields presentes)
        update_data = transacao_update.model_dump(exclude_unset=True)
        # Atualiza campos no objeto SQLAlchemy
        for key, value in update_data.items():
            if key == "valor":
                setattr(tx, key, Decimal(str(value)))
            else:
                setattr(tx, key, value)

        await db.commit()
        await db.refresh(tx)

        # Aplica efeito da transação atualizada
        await atualizar_saldo_ca(db=db, centro_academico_id=tx.centro_academico_id, valor=tx.valor, tipo=tx.tipo)

        return tx
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Falha ao atualizar transação: {str(e)}")


@router.delete("/transactions/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Apenas Tesoureiro ou Presidente podem deletar
    if current_user.cargo not in {CargoEnum.Tesoureiro, CargoEnum.Presidente}:
        raise HTTPException(status_code=403, detail="Acesso restrito à Tesouraria ou Presidência.")

    result = await db.execute(select(Transacao).where(Transacao.id == transaction_id))
    tx = result.scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transação não encontrada.")

    try:
        # Reverte efeito no saldo
        reverse_type = TipoTransacao.Despesa if tx.tipo == TipoTransacao.Receita else TipoTransacao.Receita
        await atualizar_saldo_ca(db=db, centro_academico_id=tx.centro_academico_id, valor=tx.valor, tipo=reverse_type)

        await db.delete(tx)
        await db.commit()
        return
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Falha ao remover transação: {str(e)}")
    
# Adicione isso no finance.py para a tabela do Angular carregar

@router.get("/transactions", response_model=list[TransacaoResponse])
async def list_transactions(
    limit: int = 50, # Limite para não travar o banco
    skip: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista as últimas transações para exibir no extrato simples.
    """
    query = (
        select(Transacao)
        .where(Transacao.centro_academico_id == current_user.centro_academico_id)
        .order_by(Transacao.data.desc(), Transacao.id.desc())
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(query)
    return result.scalars().all()