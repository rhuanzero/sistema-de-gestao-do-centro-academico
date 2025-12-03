from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Date, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class TipoTransacao(str, enum.Enum):
    Receita = "Receita"
    Despesa = "Despesa"

class CargoEnum(str, enum.Enum):
    Presidente = "Presidente"
    Tesoureiro = "Tesoureiro"
    Coordenador = "Coordenador"
    Membro = "Membro"

class StatusEnum(str, enum.Enum):
    Ativo = "Ativo"
    Inativo = "Inativo"

class Departamento(Base):
    __tablename__ = "departamentos"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(50), unique=True, nullable=False)
    usuarios = relationship("Usuario", back_populates="departamento")

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True)
    telefone = Column(String(20))
    cargo = Column(Enum(CargoEnum), nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.Ativo, nullable=False)
    departamento_id = Column(Integer, ForeignKey("departamentos.id"))
    
    departamento = relationship("Departamento", back_populates="usuarios")
    transacoes = relationship("Transacao", back_populates="usuario")

class CategoriaFinanceira(Base):
    __tablename__ = "categorias_financeiras"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False)
    tipo = Column(Enum(TipoTransacao), nullable=False)

class Transacao(Base):
    __tablename__ = "transacoes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    descricao = Column(String(255), nullable=False)
    valor = Column(DECIMAL(10, 2), nullable=False)
    data_transacao = Column(Date, nullable=False)
    tipo = Column(Enum(TipoTransacao), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias_financeiras.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    evento_mongo_id = Column(String(24), nullable=True) # Vínculo com Mongo

    usuario = relationship("Usuario", back_populates="transacoes")