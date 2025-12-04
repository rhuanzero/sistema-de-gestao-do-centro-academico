from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_
from app.database import get_db
from app.models.sql_models import (
    Transacao, Usuario, CargoEnum, TipoTransacao, 
    CentroAcademico, CategoriaFinanceira
)
from app.models.schemas import (
    TransacaoCreate, TransacaoResponse, TransacaoUpdate,
    CategoriaFinanceiraCreate, CategoriaFinanceiraResponse
)
from app.security import get_current_user
from datetime import date, datetime
from typing import List, Optional
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
    
    Args:
        db: Sessão do banco de dados
        centro_academico_id: ID do Centro Acadêmico
        valor: Valor da transação (sempre positivo)
        tipo: Tipo de transação (Receita/Despesa)
    """
    # Usando expressão SQL direta para atualização atômica
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
    """
    Cria uma nova transação financeira e atualiza o saldo do Centro Acadêmico.
    Apenas Tesoureiros podem registrar transações.
    """
    # Verificação de permissão
    if current_user.cargo != CargoEnum.Tesoureiro:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o Tesoureiro pode registrar transações."
        )
    
    # Verifica se a categoria pertence ao mesmo CA do usuário
    categoria = await db.get(CategoriaFinanceira, transacao.categoria_id)
    if not categoria or categoria.centro_academico_id != current_user.centro_academico_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada ou não pertence ao seu Centro Acadêmico."
        )
    
    # Verifica se o tipo da transação bate com o tipo da categoria
    if categoria.tipo.value != transacao.tipo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de transação inválido para a categoria selecionada. Esperado: {categoria.tipo}"
        )
    
    try:
        # Inicia uma transação atômica
        async with db.begin():
            # Cria a transação
            nova_transacao = Transacao(
                **transacao.model_dump(exclude={"centro_academico_id"}),
                usuario_id=current_user.id,
                centro_academico_id=current_user.centro_academico_id
            )
            db.add(nova_transacao)
            await db.flush()  # Obtém o ID da transação
            
            # Atualiza o saldo do CA
            valor_decimal = Decimal(str(transacao.valor))
            await atualizar_saldo_ca(
                db=db,
                centro_academico_id=current_user.centro_academico_id,
                valor=valor_decimal,
                tipo=TipoTransacao(transacao.tipo)
            )
            
            await db.refresh(nova_transacao)
            return nova_transacao
            
    except Exception as e:
        logger.error(f"Erro ao criar transação: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro ao processar a transação."
        )

@router.get("/balance", response_model=dict)
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
    
    # Busca o CA do usuário atual
    ca = await db.get(CentroAcademico, current_user.centro_academico_id)
    if not ca:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Centro Acadêmico não encontrado."
        )
    
    # Calcula totais para validação
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
    
    # Verificação de consistência (opcional, para debug)
    if abs(float(ca.saldo - saldo_calculado)) > 0.01:  # Tolerância para arredondamentos
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

@router.get("/report", response_model=dict)
async def generate_report(
    start_date: date, 
    end_date: date, 
    categoria_id: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """
    Gera um relatório financeiro para o período especificado.
    Apenas Tesoureiros podem gerar relatórios.
    """
    if current_user.cargo != CargoEnum.Tesoureiro:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o Tesoureiro pode gerar relatórios."
        )
    
    # Constrói a consulta base
    query = (
        select(Transacao, CategoriaFinanceira.nome.label("categoria_nome"), Usuario.nome.label("usuario_nome"))
        .join(CategoriaFinanceira, Transacao.categoria_id == CategoriaFinanceira.id)
        .join(Usuario, Transacao.usuario_id == Usuario.id)
        .where(
            Transacao.centro_academico_id == current_user.centro_academico_id,
            Transacao.data_transacao >= start_date,
            Transacao.data_transacao <= end_date
        )
    )
    
    # Filtra por categoria, se especificada
    if categoria_id is not None:
        query = query.where(Transacao.categoria_id == categoria_id)
    
    # Ordena por data
    query = query.order_by(Transacao.data_transacao.desc(), Transacao.id.desc())
    
    # Executa a consulta
    result = await db.execute(query)
    transacoes = result.all()
    
    # Calcula totais
    totais = {"receitas": Decimal('0'), "despesas": Decimal('0')}
    
    for transacao in transacoes:
        if transacao.Transacao.tipo == TipoTransacao.Receita:
            totais["receitas"] += transacao.Transacao.valor
        else:
            totais["despesas"] += transacao.Transacao.valor
    
    # Formata os resultados
    dados_formatados = []
    for transacao in transacoes:
        dados_formatados.append({
            "id": transacao.Transacao.id,
            "data": transacao.Transacao.data_transacao.isoformat(),
            "descricao": transacao.Transacao.descricao,
            "valor": float(transacao.Transacao.valor),
            "tipo": transacao.Transacao.tipo.value,
            "categoria": transacao.categoria_nome,
            "responsavel": transacao.usuario_nome,
            "evento_id": transacao.Transacao.evento_mongo_id
        })
    
    return {
        "periodo": {"inicio": start_date.isoformat(), "fim": end_date.isoformat()},
        "saldo_inicial": 0,  # Pode ser implementado se necessário
        "saldo_final": float(totais["receitas"] - totais["despes"]),
        "total_receitas": float(totais["receitas"]),
        "total_despesas": float(totais["despesas"]),
        "transacoes": dados_formatados,
        "gerado_em": datetime.now().isoformat(),
        "gerado_por": current_user.nome
    }

# Rotas para Categorias Financeiras
@router.post("/categories", response_model=CategoriaFinanceiraResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    categoria: CategoriaFinanceiraCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova categoria financeira.
    Apenas Tesoureiros podem criar categorias.
    """
    if current_user.cargo != CargoEnum.Tesoureiro:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o Tesoureiro pode criar categorias financeiras."
        )
    
    # Verifica se já existe uma categoria com o mesmo nome no mesmo CA
    existing = await db.execute(
        select(CategoriaFinanceira)
        .where(
            CategoriaFinanceira.nome == categoria.nome,
            CategoriaFinanceira.centro_academico_id == current_user.centro_academico_id
        )
    )
    
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma categoria com este nome no seu Centro Acadêmico."
        )
    
    # Cria a nova categoria
    nova_categoria = CategoriaFinanceira(
        **categoria.model_dump(),
        centro_academico_id=current_user.centro_academico_id
    )
    
    db.add(nova_categoria)
    await db.commit()
    await db.refresh(nova_categoria)
    
    return nova_categoria

@router.get("/categories", response_model=List[CategoriaFinanceiraResponse])
async def list_categories(
    tipo: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista as categorias financeiras do Centro Acadêmico.
    Filtra por tipo (Receita/Despesa) se especificado.
    """
    query = select(CategoriaFinanceira).where(
        CategoriaFinanceira.centro_academico_id == current_user.centro_academico_id
    )
    
    if tipo:
        query = query.where(CategoriaFinanceira.tipo == tipo)
    
    result = await db.execute(query)
    return result.scalars().all()
