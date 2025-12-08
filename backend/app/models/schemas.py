from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator
from typing import Optional, List, Any, Dict
from datetime import date, datetime
from enum import Enum
import re
from app.models.enums import CargoEnum, DepartamentoEnum, TipoTransacao

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
    cargo: CargoEnum = CargoEnum.Membro
    status: str = "Ativo"
    departamento_id: Optional[int] = None
    
    @field_validator('cpf')
    def validate_cpf(cls, v):
        if v is None:
            return v
        cpf = re.sub(r'\D', '', v)
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        return cpf
    
    @field_validator('telefone')
    def validate_telefone(cls, v):
        if v is None:
            return v
        telefone = re.sub(r'\D', '', v)
        if len(telefone) < 10 or len(telefone) > 11:
            raise ValueError('Telefone deve ter 10 ou 11 dígitos')
        return telefone

class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str
    cpf: str
    telefone: str
    cargo: str 
    
    # Adicione estes campos como Opcionais
    # Opcional porque o Presidente não vai ter ID para mandar no começo
    centro_academico_id: Optional[int] = None 
    departamento_id: Optional[int] = None

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None
    telefone: Optional[str] = None
    cargo: Optional[CargoEnum] = None
    status: Optional[str] = None
    departamento_id: Optional[int] = None
    senha: Optional[str] = None
    centro_academico_id: Optional[int] = None

class UsuarioResponse(UsuarioBase):
    id: int
    centro_academico_id: int
    
    model_config = ConfigDict(from_attributes=True)

# --- Schemas de Transação ---
class TransacaoBase(BaseModel):
    descricao: str
    valor: float = Field(..., gt=0)
    data: datetime
    tipo: str = Field(pattern="^(Receita|Despesa)$")

class TransacaoCreate(TransacaoBase):
    pass

class TransacaoUpdate(BaseModel):
    descricao: Optional[str] = None
    valor: Optional[float] = None
    data: Optional[datetime] = None
    tipo: Optional[str] = Field(None, pattern="^(Receita|Despesa)$")

class TransacaoResponse(TransacaoBase):
    id: int
    usuario_id: int
    centro_academico_id: int

    model_config = ConfigDict(from_attributes=True)

# --- Schemas MongoDB (Eventos/Posts) ---
class Tarefa(BaseModel):
    id_interno: int
    descricao: str
    status: str = "Pendente"
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
    status: str = "Rascunho"

    @field_validator('data_inicio', mode='before')
    def ensure_datetime_for_start(cls, v):
        return v

    @field_validator('data_fim', mode='before')
    def ensure_datetime_for_end(cls, v):
        return v

    @classmethod
    @model_validator(mode='after')
    def validate_dates(cls, model):
        data_inicio = model.data_inicio
        data_fim = model.data_fim
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if data_inicio < today_start:
            raise ValueError('A data de início não pode ser no passado.')

        if data_fim < data_inicio:
            raise ValueError('A data de fim deve ser igual ou posterior à data de início.')

        return model

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

class SolicitacaoComunicacaoResponse(BaseModel):
    id: str
    titulo: str
    descricao: str
    prazo_sugerido: datetime
    publico_alvo: str
    solicitante_id: int
    solicitante_nome: str
    data_solicitacao: datetime
    status: str
    
class Token(BaseModel):
    access_token: str
    token_type: str
    # ADICIONE ESSES CAMPOS PARA O FRONT RECEBER:
    user_id: int
    cargo: str 
    centro_academico_id: Optional[int] = None

# --- Schemas de Patrimônio (MongoDB) ---
# 👇 AQUI ESTAVA O PROBLEMA: Atualizei para incluir valor, tombo e localizacao
class HistoricoItem(BaseModel):
    timestamp: datetime
    usuario_id: int
    acao: str
    detalhes: Optional[str] = None

class PatrimonioBase(BaseModel):
    nome: str
    tombo: Optional[str] = None
    
    # 👇 AQUI ESTÁ A CORREÇÃO: Adicione " = 0.0"
    valor: float = 0.0 
    
    localizacao: Optional[str] = None
    descricao: Optional[str] = None
    status: str = "Disponível" 
    data_aquisicao: Optional[date] = None
    historico: List[HistoricoItem] = []

class PatrimonioCreate(PatrimonioBase):
    pass

class PatrimonioUpdate(BaseModel):
    nome: Optional[str] = None
    tombo: Optional[str] = None       # <--- Adicionado
    valor: Optional[float] = None     # <--- Adicionado
    localizacao: Optional[str] = None # <--- Adicionado
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
    
# ... (Mantenha os imports e outras classes) ...

# --- ATUALIZE AS CLASSES DE COMUNICAÇÃO ---

class PostagemCreate(BaseModel):
    titulo: str
    conteudo_texto: str
    midia_destino: str
    data_agendamento: datetime
    anexos: List[str] = []

class PostagemUpdate(BaseModel):
    titulo: Optional[str] = None
    conteudo_texto: Optional[str] = None
    midia_destino: Optional[str] = None
    data_agendamento: Optional[datetime] = None
    anexos: Optional[List[str]] = None
    status: Optional[str] = None  # 👈 Permite mudar status

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

class SolicitacaoComunicacaoCreate(BaseModel):
    titulo: str
    descricao: str
    prazo_sugerido: date
    publico_alvo: str

class SolicitacaoComunicacaoUpdate(BaseModel): # 👈 Necessário para editar docs
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    prazo_sugerido: Optional[date] = None
    publico_alvo: Optional[str] = None
    status: Optional[str] = None  # 👈 Permite mudar status

class SolicitacaoComunicacaoResponse(BaseModel):
    id: str
    titulo: str
    descricao: str
    prazo_sugerido: datetime
    publico_alvo: str
    solicitante_id: int
    solicitante_nome: str
    data_solicitacao: datetime
    status: str