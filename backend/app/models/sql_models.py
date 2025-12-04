from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DECIMAL, TIMESTAMP, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime
from enum import IntEnum

class TipoTransacao(str, enum.Enum):
    Receita = "Receita"
    Despesa = "Despesa"

class CargoEnum(str, enum.Enum):
    Presidente = "Presidente"
    Tesoureiro = "Tesoureiro"
    Coordenador = "Coordenador"
    Membro = "Membro"

class DepartamentoEnum(IntEnum):
    Presidencia = 1
    Financeiro = 2
    Eventos = 3
    Comunicacao = 4
    Patrimonio = 5
    def __int__(self):
        return self.value

class StatusEnum(str, enum.Enum):
    Ativo = "Ativo"
    Inativo = "Inativo"

class CentroAcademico(Base):
    __tablename__ = "centro_academico"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    saldo = Column(DECIMAL(15, 2), default=0.00, nullable=False)
    data_criacao = Column(TIMESTAMP, server_default=func.now())
    
    # Relacionamentos
    departamentos = relationship("Departamento", back_populates="centro_academico", cascade="all, delete-orphan")
    usuarios = relationship("Usuario", back_populates="centro_academico", cascade="all, delete-orphan")
    transacoes = relationship("Transacao", back_populates="centro_academico", cascade="all, delete-orphan")

class Departamento(Base):
    __tablename__ = "departamentos"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(50), nullable=False)
    
    # Relacionamento com Centro Acadêmico
    centro_academico_id = Column(Integer, ForeignKey("centro_academico.id"), nullable=False)
    centro_academico = relationship("CentroAcademico", back_populates="departamentos")
    
    # Relacionamento com Usuários
    usuarios = relationship("Usuario", back_populates="departamento")

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True, nullable=True)
    telefone = Column(String(20), nullable=True)
    cargo = Column(Enum(CargoEnum), nullable=False, default=CargoEnum.Membro)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.Ativo)
    
    # Chaves estrangeiras
    departamento_id = Column(Integer, ForeignKey('departamentos.id'), nullable=True)
    centro_academico_id = Column(Integer, ForeignKey('centro_academico.id'), nullable=False)
    
    # Relacionamentos
    departamento = relationship("Departamento", back_populates="usuarios")
    centro_academico = relationship("CentroAcademico", back_populates="usuarios")
    transacoes = relationship("Transacao", back_populates="usuario")

    def __repr__(self):
        return f"<Usuario(id={self.id}, nome='{self.nome}', email='{self.email}')>"

class Transacao(Base):
    __tablename__ = "transacoes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    descricao = Column(String(200), nullable=False)
    valor = Column(DECIMAL(15, 2), nullable=False)
    tipo = Column(Enum(TipoTransacao), nullable=False)
    data = Column(DateTime, default=func.now(), nullable=False)
    
    # Chaves estrangeiras
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    centro_academico_id = Column(Integer, ForeignKey('centro_academico.id'), nullable=False)
     
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="transacoes")
    centro_academico = relationship("CentroAcademico", back_populates="transacoes")

    def __repr__(self):
        return f"<Transacao(id={self.id}, descricao='{self.descricao}', valor={self.valor})>"