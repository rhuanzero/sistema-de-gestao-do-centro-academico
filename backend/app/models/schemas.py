from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, List, Any, Dict
from datetime import date, datetime
from enum import Enum
import re

# --- Enums para reutilização ---
class Cargo(str, Enum):
    Presidente = "Presidente"
    Tesoureiro = "Tesoureiro"
    Coordenador = "Coordenador"
    Membro = "Membro"

# --- Schemas de Centro Acadêmico ---
class CentroAcademicoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None

class CentroAcademicoCreate(CentroAcademicoBase):
    pass

class CentroAcademicoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    data_fundacao: Optional[date] = None

class CentroAcademicoResponse(CentroAcademicoBase):
    id: int
    saldo: float
    data_criacao: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Schemas de Departamento ---
class DepartamentoBase(BaseModel):
    nome: str
    centro_academico_id: int

class DepartamentoCreate(DepartamentoBase):
    pass

class DepartamentoResponse(DepartamentoBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# --- Schemas de Usuário ---
class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    cpf: Optional[str] = None
    telefone: Optional[str] = None
    cargo: Cargo = Cargo.Membro
    status: str = "Ativo"
    departamento_id: Optional[int] = None
    centro_academico_id: int
    
    @field_validator('cpf')
    def validate_cpf(cls, v):
        if v is None:
            return v
        # Remove caracteres não numéricos
        cpf = re.sub(r'\D', '', v)
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        return cpf
    
    @field_validator('telefone')
    def validate_telefone(cls, v):
        if v is None:
            return v
        # Remove caracteres não numéricos
        telefone = re.sub(r'\D', '', v)
        if len(telefone) < 10 or len(telefone) > 11:
            raise ValueError('Telefone deve ter 10 ou 11 dígitos')
        return telefone

class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=6, max_length=100)

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None
    telefone: Optional[str] = None
    cargo: Optional[Cargo] = None
    status: Optional[str] = None
    departamento_id: Optional[int] = None
    senha: Optional[str] = None
    centro_academico_id: Optional[int] = None

class UsuarioResponse(UsuarioBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# --- Schemas de Transação ---
class TransacaoBase(BaseModel):
    descricao: str
    valor: float = Field(..., gt=0)
    data: datetime
    tipo: str = Field(pattern="^(Receita|Despesa)$")
    usuario_id: int 
    centro_academico_id: int = 1

class TransacaoCreate(TransacaoBase):
    pass

class TransacaoUpdate(BaseModel):
    descricao: Optional[str] = None
    valor: Optional[float] = None
    data: Optional[datetime] = None
    tipo: Optional[str] = Field(None, pattern="^(Receita|Despesa)$")

class TransacaoResponse(TransacaoBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# --- Schemas MongoDB (Eventos/Posts) ---
class Tarefa(BaseModel):
    id_interno: int
    descricao: str
    status: str = "Pendente" # Pendente, Concluida
    usuario_responsavel_id: int

class Patrocinio(BaseModel):
    nome_empresa: str
    tipo: str
    valor: float
    contato: str
    status_pagamento: str

class EventoCreate(BaseModel):
    titulo: str
    descricao: str
    local: str
    data_inicio: datetime
    data_fim: datetime
    orcamento_limite: Optional[float] = None
    responsaveis_ids: List[int]
    status: str = "Em Planejamento"

class PostagemCreate(BaseModel):
    titulo: str
    conteudo_texto: str
    midia_destino: str
    data_agendamento: datetime
    anexos: List[str] = []

class SolicitacaoComunicacaoCreate(BaseModel):
    titulo: str
    descricao: str
    prazo_sugerido: date
    publico_alvo: str
    
class Token(BaseModel):
    access_token: str
    token_type: str

# --- Schemas de Patrimônio (MongoDB) ---
class HistoricoItem(BaseModel):
    timestamp: datetime
    usuario_id: int
    acao: str
    detalhes: Optional[str] = None

class PatrimonioBase(BaseModel):
    nome: str
    descricao: str
    status: str = "Disponível" # Disponível, Em uso, Manutenção, Baixado
    data_aquisicao: date
    historico: List[HistoricoItem] = []

class PatrimonioCreate(PatrimonioBase):
    pass

class PatrimonioUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    status: Optional[str] = None
    data_aquisicao: Optional[date] = None

class PatrimonioResponse(PatrimonioBase):
    id: str

    class Config:
        from_attributes = True

# --- Schemas de resposta e updates para Eventos/Postagens/Relatórios ---
class EventoUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    local: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    orcamento_limite: Optional[float] = None
    responsaveis_ids: Optional[List[int]] = None
    status: Optional[str] = None


class EventoResponse(BaseModel):
    id: str
    titulo: str
    descricao: str
    local: str
    data_inicio: datetime
    data_fim: datetime
    orcamento_limite: Optional[float] = None
    responsaveis_ids: List[int]
    status: str
    tarefas: List[Tarefa] = []
    patrocinios: List[Patrocinio] = []
    criado_em: Optional[datetime] = None
    criado_por: Optional[Dict[str, Any]] = None


class PostagemUpdate(BaseModel):
    titulo: Optional[str] = None
    conteudo_texto: Optional[str] = None
    midia_destino: Optional[str] = None
    data_agendamento: Optional[datetime] = None
    anexos: Optional[List[str]] = None
    status: Optional[str] = None


class PostagemResponse(BaseModel):
    id: str
    titulo: str
    conteudo_texto: str
    midia_destino: str
    data_agendamento: datetime
    anexos: List[str]
    autor_id: int
    status: str
    criado_em: Optional[datetime] = None


class BalanceResponse(BaseModel):
    saldo_atual: float
    receitas: float
    despesas: float
    ultima_atualizacao: str


class ReportTransaction(BaseModel):
    id: int
    data: str
    descricao: str
    valor: float
    tipo: str
    responsavel: str


class ReportResponse(BaseModel):
    periodo: Dict[str, str]
    total_receitas: float
    total_despesas: float
    saldo_periodo: float
    transacoes: List[ReportTransaction]
    total_registros: int
    gerado_em: str


# --- Schemas comuns de criação/mensagem ---
class CreatedResponse(BaseModel):
    id: str
    message: str


class CreatedWithStatus(BaseModel):
    id: str
    status: str


class TaskCreatedResponse(BaseModel):
    message: str
    task_id: int


class SimpleMessageResponse(BaseModel):
    message: str


class MessageStatusResponse(BaseModel):
    message: str
    novo_status: Optional[str] = None