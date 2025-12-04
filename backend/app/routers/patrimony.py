from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from datetime import datetime, date
from app.database import get_mongo_db
from app.models.schemas import PatrimonioCreate, PatrimonioUpdate, PatrimonioResponse, HistoricoItem
from app.security import get_current_user
from app.models.sql_models import Usuario, CargoEnum

router = APIRouter(prefix="/patrimony", tags=["Gestão de Patrimônio"])

@router.post("/", response_model=PatrimonioResponse, status_code=status.HTTP_201_CREATED)
async def create_patrimony_item(
    item: PatrimonioCreate,
    db = Depends(get_mongo_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.cargo not in [CargoEnum.Presidente, CargoEnum.Coordenador]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    item_dict = item.model_dump()
    # Converte date para datetime para ser compatível com BSON/MongoDB
    if isinstance(item_dict.get("data_aquisicao"), date) and not isinstance(item_dict.get("data_aquisicao"), datetime):
        item_dict["data_aquisicao"] = datetime.combine(item_dict["data_aquisicao"], datetime.min.time())

    # Adiciona o registro inicial ao histórico
    item_dict["historico"] = [{
        "timestamp": datetime.utcnow(),
        "usuario_id": current_user.id,
        "acao": "Criação",
        "detalhes": f"Item criado por {current_user.nome}."
    }]

    result = await db.patrimonio.insert_one(item_dict)
    
    created_item = await db.patrimonio.find_one({"_id": result.inserted_id})
    created_item["id"] = str(created_item["_id"])
    return created_item

@router.get("/", response_model=List[PatrimonioResponse])
async def list_patrimony_items(db = Depends(get_mongo_db)):
    items = []
    cursor = db.patrimonio.find()
    async for item in cursor:
        item["id"] = str(item["_id"])
        items.append(item)
    return items

@router.get("/{item_id}", response_model=PatrimonioResponse)
async def get_patrimony_item(item_id: str, db = Depends(get_mongo_db)):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de item inválido.")

    item = await db.patrimonio.find_one({"_id": ObjectId(item_id)})
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de patrimônio não encontrado.")
    
    item["id"] = str(item["_id"])
    return item

@router.put("/{item_id}", response_model=PatrimonioResponse)
async def update_patrimony_item(
    item_id: str,
    update_data: PatrimonioUpdate,
    db = Depends(get_mongo_db),
    current_user: Usuario = Depends(get_current_user)
):
    # RF16: Membros, Coordenadores e Presidente podem alterar status e localização
    if current_user.cargo not in [CargoEnum.Presidente, CargoEnum.Coordenador, CargoEnum.Membro]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de item inválido.")

    update_dict = {k: v for k, v in update_data.model_dump(exclude_unset=True).items()}

    # Converte date para datetime se o campo estiver presente na atualização
    if 'data_aquisicao' in update_dict and isinstance(update_dict['data_aquisicao'], date) and not isinstance(update_dict['data_aquisicao'], datetime):
        update_dict['data_aquisicao'] = datetime.combine(update_dict['data_aquisicao'], datetime.min.time())

    if not update_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum dado para atualizar.")

    # Cria o registro de histórico
    historico_entry = {
        "timestamp": datetime.utcnow(),
        "usuario_id": current_user.id,
        "acao": "Atualização",
        "detalhes": f"Campos atualizados: {', '.join(update_dict.keys())}"
    }

    result = await db.patrimonio.update_one(
        {"_id": ObjectId(item_id)},
        {
            "$set": update_dict,
            "$push": {"historico": historico_entry}
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de patrimônio não encontrado.")

    updated_item = await db.patrimonio.find_one({"_id": ObjectId(item_id)})
    updated_item["id"] = str(updated_item["_id"])
    return updated_item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patrimony_item(
    item_id: str,
    db = Depends(get_mongo_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.cargo not in [CargoEnum.Presidente, CargoEnum.Coordenador]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de item inválido.")

    result = await db.patrimonio.delete_one({"_id": ObjectId(item_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de patrimônio não encontrado.")

@router.get("/{item_id}/history", response_model=List[HistoricoItem])
async def get_patrimony_history(item_id: str, db = Depends(get_mongo_db)):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de item inválido.")

    item = await db.patrimonio.find_one(
        {"_id": ObjectId(item_id)},
        {"historico": 1, "_id": 0}  # Projeta apenas o campo historico
    )

    if not item or "historico" not in item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Histórico não encontrado para este item.")

    return item["historico"]
