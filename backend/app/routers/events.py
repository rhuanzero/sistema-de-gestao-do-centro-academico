from fastapi import APIRouter, Depends, HTTPException, Body
from app.database import get_mongo_db
from app.models.schemas import EventoCreate, Tarefa
from app.security import get_current_user
from app.models.sql_models import Usuario, CargoEnum
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
    db = Depends(get_mongo_db)
):
    # Coordenador adiciona tarefas
    if current_user.cargo != CargoEnum.Coordenador:
        raise HTTPException(status_code=403, detail="Apenas Coordenadores adicionam tarefas.")

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