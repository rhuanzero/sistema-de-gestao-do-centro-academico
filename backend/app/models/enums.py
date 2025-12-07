# app/models/enums.py
import enum
from enum import IntEnum

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

class DepartamentoEnum(IntEnum):
    Presidencia = 1
    Financeiro = 2
    Eventos = 3
    Comunicacao = 4
    Patrimonio = 5