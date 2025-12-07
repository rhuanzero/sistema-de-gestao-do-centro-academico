from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_mongo_db, get_db
from app.models.schemas import (
    EventoCreate,
    EventoUpdate,
    EventoResponse,
    Tarefa,
    Patrocinio,
    CreatedResponse,
    TaskCreatedResponse,
    SimpleMessageResponse,
    MessageStatusResponse,
)
from app.security import get_current_user
from app.models.sql_models import Usuario, CargoEnum, Departamento
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/events", tags=["Gestão de Eventos"])

@router.post("/", response_model=CreatedResponse)
async def create_event(
    evento: EventoCreate,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    # Regra simples: Coordenadores e Presidente
    if current_user.cargo not in [CargoEnum.Coordenador, CargoEnum.Presidente]:
        raise HTTPException(status_code=403, detail="Permissão insuficiente.")
    
    # Verifica se já existe um evento com o mesmo título
    existing = await db.eventos.find_one({"titulo": {"$regex": f"^{evento.titulo}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=400, detail="Já existe um evento com este título")
    
    evento_dict = evento.dict()
    evento_dict["tarefas"] = []  # Inicia lista vazia
    evento_dict["patrocinios"] = []
    evento_dict["criado_em"] = datetime.utcnow()
    evento_dict["criado_por"] = {
        "id": str(current_user.id),
        "nome": current_user.nome
    }
    
    new_event = await db.eventos.insert_one(evento_dict)
    return {"id": str(new_event.inserted_id), "message": "Evento criado com sucesso"}


@router.put("/{evento_titulo}", response_model=EventoResponse)
async def update_event(
    evento_titulo: str,
    update_data: EventoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    # Permissão: Coordenador ou Presidente
    if current_user.cargo not in [CargoEnum.Coordenador, CargoEnum.Presidente]:
        raise HTTPException(status_code=403, detail="Permissão insuficiente para atualizar evento.")

    evento = await db.eventos.find_one({"titulo": {"$regex": f"^{evento_titulo}$", "$options": "i"}})
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    # Sanitiza campos e aplica atualização
    update_dict = {k: v for k, v in update_data.items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")

    result = await db.eventos.update_one({"_id": evento["_id"]}, {"$set": update_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Falha ao atualizar evento")

    updated = await db.eventos.find_one({"_id": evento["_id"]})
    updated["id"] = str(updated["_id"])
    del updated["_id"]
    return updated


@router.delete("/{evento_titulo}", status_code=204)
async def delete_event(
    evento_titulo: str,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    # Apenas Presidente pode deletar eventos
    if current_user.cargo != CargoEnum.Presidente:
        raise HTTPException(status_code=403, detail="Apenas o Presidente pode deletar eventos.")

    evento = await db.eventos.find_one({"titulo": {"$regex": f"^{evento_titulo}$", "$options": "i"}})
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    result = await db.eventos.delete_one({"_id": evento["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Falha ao deletar evento")
    return

@router.get("/", response_model=list[EventoResponse])
async def list_events(
    db = Depends(get_mongo_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Busca todos os eventos ordenados por data de criação (mais recentes primeiro)
    events = await db.eventos.find().sort("criado_em", -1).to_list(length=1000)
    
    # Processamento para serialização
    results = []
    for event in events:
        event["id"] = str(event["_id"])
        del event["_id"]
        results.append(event)
        
    return results

@router.get("/{evento_titulo}", response_model=EventoResponse)
async def get_event(
    evento_titulo: str,
    db = Depends(get_mongo_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Busca o evento pelo título exato (case-insensitive)
    event = await db.eventos.find_one({"titulo": {"$regex": f"^{evento_titulo}$", "$options": "i"}})
    
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    # Converte o ObjectId para string
    event["id"] = str(event["_id"])
    del event["_id"]
    
    return event

@router.post("/{evento_titulo}/tasks", response_model=TaskCreatedResponse)
async def add_task_to_event(
    evento_titulo: str,
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
    elif current_user.cargo != CargoEnum.Presidente and current_user.cargo != CargoEnum.Coordenador:
        raise HTTPException(status_code=403, detail="Permissão insuficiente para adicionar tarefas.")

    try:
        # Busca o evento pelo título (case-insensitive)
        evento = await db.eventos.find_one({"titulo": {"$regex": f"^{evento_titulo}$", "$options": "i"}})
        
        if not evento:
            raise HTTPException(status_code=404, detail="Evento não encontrado")

        # Gera um ID único para a tarefa
        task_id = len(evento.get("tarefas", [])) + 1

        # Adiciona a tarefa ao array de tarefas do evento
        result = await db.eventos.update_one(
            {"_id": evento["_id"]},
            {"$push": {
                "tarefas": {
                    **tarefa.dict(),
                    "id_interno": task_id,
                    "criado_em": datetime.utcnow(),
                    "criado_por": {
                        "id": str(current_user.id),
                        "nome": current_user.nome
                    }
                }
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Falha ao adicionar tarefa ao evento")
            
        return {"message": "Tarefa adicionada com sucesso", "task_id": task_id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar a requisição: {str(e)}")

@router.put("/{evento_titulo}/tasks/{task_id}/status", response_model=MessageStatusResponse)
async def update_task_status(
    evento_titulo: str,
    task_id: int,
    status: str = Body(..., embed=True),
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    # Encontra o evento pelo título
    evento = await db.eventos.find_one({"titulo": {"$regex": f"^{evento_titulo}$", "$options": "i"}})
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    # Verifica se o usuário tem permissão (Presidente, Coordenador ou é o responsável)
    is_allowed = (current_user.cargo in [CargoEnum.Presidente, CargoEnum.Coordenador])
    
    # Se não for Presidente nem Coordenador, verifica se é o responsável pela tarefa
    if not is_allowed:
        # Encontra a tarefa específica
        for task in evento.get("tarefas", []):
            if task.get("id_interno") == task_id:
                if task.get("usuario_responsavel_id") == current_user.id:
                    is_allowed = True
                break

    if not is_allowed:
        raise HTTPException(
            status_code=403, 
            detail="Apenas o Presidente, Coordenador ou o responsável pela tarefa podem atualizar o status"
        )

    # Atualiza o status da tarefa
    result = await db.eventos.update_one(
        {
            "_id": evento["_id"],
            "tarefas.id_interno": task_id
        },
        {
            "$set": {
                "tarefas.$.status": status,
                "tarefas.$.atualizado_em": datetime.utcnow(),
                "tarefas.$.atualizado_por": {
                    "id": str(current_user.id),
                    "nome": current_user.nome,
                    "cargo": current_user.cargo.value
                }
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
            
    return {"message": "Status atualizado com sucesso", "novo_status": status}

    
@router.post("/{evento_titulo}/sponsors", response_model=SimpleMessageResponse)
async def add_sponsor_to_event(
    evento_titulo: str,
    patrocinio: Patrocinio,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    if current_user.cargo not in [CargoEnum.Coordenador, CargoEnum.Presidente]:
        raise HTTPException(status_code=403, detail="Permissão insuficiente.")

    # Encontra o evento pelo título
    evento = await db.eventos.find_one({"titulo": {"$regex": f"^{evento_titulo}$", "$options": "i"}})
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    # Adiciona o patrocínio
    result = await db.eventos.update_one(
        {"_id": evento["_id"]},
        {
            "$push": {
                "patrocinios": {
                    **patrocinio.dict(),
                    "adicionado_em": datetime.utcnow(),
                    "adicionado_por": {
                        "id": str(current_user.id),
                        "nome": current_user.nome
                    }
                }
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Falha ao adicionar patrocínio ao evento")

    return {"message": "Patrocínio adicionado com sucesso."}