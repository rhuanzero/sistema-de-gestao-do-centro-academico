from typing import Optional
from fastapi import Depends
from app.security import get_current_user
from app.models.sql_models import Usuario

def get_current_centro_academico_id(
    centro_academico_id: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user)
) -> int:
    """Retorna o centro_academico_id que deve ser usado para a operação.

    - Se um `centro_academico_id` for passado explicitamente (ex.: administrador),
      o comportamento atual é **ignorar** este valor e sempre retornar o
      `current_user.centro_academico_id` para garantir que clientes não possam
      operar em outros centros acadêmicos.
    - Esta função facilita a substituição futura do comportamento (por exemplo,
      permitir administradores a especificar outro CA) em um único lugar.
    """
    return current_user.centro_academico_id
