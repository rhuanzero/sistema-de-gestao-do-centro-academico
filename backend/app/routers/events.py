from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_mongo_db, get_db
from app.models.schemas import EventoCreate, Tarefa, Patrocinio
from app.security import get_current_user
from app.models.sql_models import Usuario, CargoEnum, Departamento
from bson import ObjectId

router = APIRouter(prefix="/events", tags=["Gestão de Eventos"])

@router.post("/")
async def create_event(
    evento: EventoCreate,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    # Regra simples: Coordenadores e Presidente
    if current_user.cargo not in [CargoEnum.Coordenador, CargoEnum.Presidente]:
        raise HTTPException(status_code=403, detail="Permissão insuficiente.")
    
    evento_dict = evento.model_dump()
    evento_dict["tarefas"] = [] # Inicia lista vazia
    evento_dict["patrocinios"] = []
    
    new_event = await db.eventos.insert_one(evento_dict)
    return {"id": str(new_event.inserted_id), "message": "Evento criado com sucesso"}

@router.post("/{evento_id}/tasks")
async def add_task_to_event(
    evento_id: str,
    tarefa: Tarefa,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db),
    sql_db: AsyncSession = Depends(get_db)
):
    # RN03: Validação de departamento para Coordenadores
    if current_user.cargo == CargoEnum.Coordenador:
        # Busca o usuário responsável pela tarefa no banco SQL
        result = await sql_db.execute(select(Usuario).where(Usuario.id == tarefa.usuario_responsavel_id))
        responsavel = result.scalars().first()

        if not responsavel:
            raise HTTPException(status_code=404, detail="Usuário responsável pela tarefa não encontrado.")

        if responsavel.departamento_id != current_user.departamento_id:
            raise HTTPException(status_code=403, detail="Coordenadores só podem atribuir tarefas a membros do seu próprio departamento.")
    elif current_user.cargo != CargoEnum.Presidente:
        raise HTTPException(status_code=403, detail="Permissão insuficiente para adicionar tarefas.")

    result = await db.eventos.update_one(
        {"_id": ObjectId(evento_id)},
        {"$push": {"tarefas": tarefa.model_dump()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return {"message": "Tarefa adicionada"}

@router.put("/{evento_id}/tasks/{task_internal_id}/status") # UC05
async def update_task_status(
    evento_id: str,
    task_internal_id: int,
    status: str = Body(..., embed=True),
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    # Membro atualiza tarefa
    filter_query = {
        "_id": ObjectId(evento_id),
        "tarefas.id_interno": task_internal_id,
        "tarefas.usuario_responsavel_id": current_user.id # Apenas a própria tarefa
    }
    
    update_query = {
        "$set": {"tarefas.$.status": status}
    }
    
    result = await db.eventos.update_one(filter_query, update_query)
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Tarefa não encontrada ou não pertence a você.")
        
    return {"message": "Status atualizado", "novo_status": status}

@router.post("/{evento_id}/sponsors")
async def add_sponsor_to_event(
    evento_id: str,
    patrocinio: Patrocinio,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    if current_user.cargo not in [CargoEnum.Coordenador, CargoEnum.Presidente]:
        raise HTTPException(status_code=403, detail="Permissão insuficiente.")

    if not ObjectId.is_valid(evento_id):
        raise HTTPException(status_code=400, detail="ID de evento inválido.")

    result = await db.eventos.update_one(
        {"_id": ObjectId(evento_id)},
        {"$push": {"patrocinios": patrocinio.model_dump()}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    return {"message": "Patrocínio adicionado com sucesso."}

@router.get("/list_events")
async def list_events(
    db = Depends(get_mongo_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Busca os eventos no MongoDB (limite de 1000 para evitar sobrecarga em testes)
    events = await db.eventos.find().to_list(length=1000)
    
    # Processamento para serialização
    results = []
    for event in events:
        # Converte o ObjectId para string para que o JSON possa ser gerado
        event["id"] = str(event["_id"])
        del event["_id"] # Remove o objeto original que causa erro
        results.append(event)
        
    return results