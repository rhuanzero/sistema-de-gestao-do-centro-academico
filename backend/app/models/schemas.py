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

# --- Schemas de Categoria Financeira ---
class CategoriaFinanceiraBase(BaseModel):
    nome: str
    tipo: str = Field(pattern="^(Receita|Despesa)$")
    centro_academico_id: int

class CategoriaFinanceiraCreate(CategoriaFinanceiraBase):
    pass

class CategoriaFinanceiraResponse(CategoriaFinanceiraBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# --- Schemas de Transação ---
class TransacaoBase(BaseModel):
    descricao: str
    valor: float = Field(..., gt=0)
    data: datetime
    tipo: str = Field(pattern="^(Receita|Despesa)$")
    categoria_id: int
    usuario_id: int
    centro_academico_id: int

class TransacaoCreate(TransacaoBase):
    pass

class TransacaoUpdate(BaseModel):
    descricao: Optional[str] = None
    valor: Optional[float] = None
    data: Optional[datetime] = None
    tipo: Optional[str] = Field(None, pattern="^(Receita|Despesa)$")
    categoria_id: Optional[int] = None

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