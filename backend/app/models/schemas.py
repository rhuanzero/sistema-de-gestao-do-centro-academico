from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import date, datetime
from enum import Enum

# --- Enums para reutilização ---
class Cargo(str, Enum):
    Presidente = "Presidente"
    Tesoureiro = "Tesoureiro"
    Coordenador = "Coordenador"
    Membro = "Membro"

# --- Schemas de Usuário (MySQL) ---
class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    cpf: Optional[str] = None
    telefone: Optional[str] = None
    cargo: Cargo
    departamento_id: Optional[int] = None

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioResponse(UsuarioBase):
    id: int
    status: str
    class Config:
        from_attributes = True

# --- Schemas Financeiros (MySQL) ---
class TransacaoCreate(BaseModel):
    descricao: str
    valor: float
    data_transacao: date
    tipo: str = Field(pattern="^(Receita|Despesa)$")
    categoria_id: int
    evento_mongo_id: Optional[str] = None

class TransacaoResponse(TransacaoCreate):
    id: int
    usuario_id: int
    class Config:
        from_attributes = True

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
    orcamento_maximo: float
    responsaveis_ids: List[int]
    status: str = "Em Planejamento"

class PostagemCreate(BaseModel):
    titulo: str
    conteudo_texto: str
    midia_destino: str
    data_agendamento: datetime
    anexos: List[str] = []
    
class Token(BaseModel):
    access_token: str
    token_type: str