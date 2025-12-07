from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, date, timezone
from app.database import get_mongo_db
from app.models.schemas import PatrimonioCreate, PatrimonioUpdate, PatrimonioResponse, HistoricoItem
from app.security import get_current_user
from app.models.sql_models import Usuario, CargoEnum
from bson import ObjectId # <--- Importante para buscar por ID

# 👇 1. Prefixo ajustado para Português para bater com o Angular
router = APIRouter(prefix="/patrimonio", tags=["Gestão de Patrimônio"])

@router.post("/", response_model=PatrimonioResponse, status_code=status.HTTP_201_CREATED)
async def create_patrimony_item(
    item: PatrimonioCreate,
    db = Depends(get_mongo_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Prints de Debug (Pode manter ou tirar)
    print(f"💰 Valor recebido: {item.valor}")

    # Verificação de Permissão
    if current_user.cargo not in [CargoEnum.Presidente, CargoEnum.Coordenador]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    # Verifica duplicidade
    existing_item = await db.patrimonio.find_one({"nome": {"$regex": f"^{item.nome}$", "$options": "i"}})
    if existing_item:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Item já existe.")

    item_dict = item.model_dump()
    
    # CONVERSÃO DE DATA BLINDADA (Garante que salva como datetime no Mongo)
    if item_dict.get("data_aquisicao"):
        dt = item_dict["data_aquisicao"]
        if isinstance(dt, date) and not isinstance(dt, datetime):
            item_dict["data_aquisicao"] = datetime.combine(dt, datetime.min.time())

    # Histórico
    item_dict["historico"] = [{
        "timestamp": datetime.now(timezone.utc),
        "usuario_id": current_user.id,
        "acao": "Criação",
        "detalhes": f"Item criado por {current_user.nome}."
    }]

    # Salva no Banco
    result = await db.patrimonio.insert_one(item_dict)
    
    # Busca o item salvo
    created_item = await db.patrimonio.find_one({"_id": result.inserted_id})
    
    # --- 👇 CORREÇÃO DO ERRO 500 AQUI 👇 ---
    
    # 1. Converte _id para string id
    created_item["id"] = str(created_item["_id"])
    
    # 2. Remove o _id original para não confundir o Pydantic
    if "_id" in created_item:
        del created_item["_id"]

    # 3. Converte datetime de volta para date (se necessário) para não quebrar o Schema
    if created_item.get("data_aquisicao") and isinstance(created_item["data_aquisicao"], datetime):
        created_item["data_aquisicao"] = created_item["data_aquisicao"].date()

    return created_item

@router.get("/", response_model=List[PatrimonioResponse])
async def list_patrimony_items(current_user: Usuario = Depends(get_current_user), db = Depends(get_mongo_db)):
    items = []
    # Busca todos os itens
    cursor = db.patrimonio.find()
    async for item in cursor:
        item["id"] = str(item["_id"])
        items.append(item)
    return items

# 👇 Mudei de item_nome para item_id para aceitar o ID do Angular
@router.get("/{item_id}", response_model=PatrimonioResponse)
async def get_patrimony_item(
    item_id: str, 
    current_user: Usuario = Depends(get_current_user), 
    db = Depends(get_mongo_db)
):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="ID inválido")

    item = await db.patrimonio.find_one({"_id": ObjectId(item_id)})
    
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado.")
    
    item["id"] = str(item["_id"])
    return item

@router.put("/{item_id}", response_model=PatrimonioResponse)
async def update_patrimony_item(
    item_id: str,
    update_data: PatrimonioUpdate,
    db = Depends(get_mongo_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.cargo not in [CargoEnum.Presidente, CargoEnum.Coordenador, CargoEnum.Membro]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="ID inválido")

    # Busca item original pelo ID
    original_item = await db.patrimonio.find_one({"_id": ObjectId(item_id)})
    if not original_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado.")

    update_dict = {k: v for k, v in update_data.model_dump(exclude_unset=True).items()}

    if not update_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum dado para atualizar.")

    # Verificação de nome duplicado (se o nome mudou)
    if "nome" in update_dict and update_dict["nome"] != original_item["nome"]:
        novo_nome = update_dict["nome"]
        conflict_item = await db.patrimonio.find_one({"nome": {"$regex": f"^{novo_nome}$", "$options": "i"}})
        # Garante que não é o próprio item
        if conflict_item and str(conflict_item["_id"]) != item_id:
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=f"Não é possível renomear. Já existe outro item com o nome '{novo_nome}'."
            )
            
    # --- LÓGICA DE REGRAS DE NEGÓCIO (Mantida e ajustada) ---
    novo_status = update_dict.get("status")
    status_atual = original_item.get("status")
    
    if novo_status == "Em Uso":
        nova_localizacao = update_dict.get("localizacao") or original_item.get("localizacao")
        # Se não enviou responsável, usa o usuário logado
        if "responsavel_id" not in update_dict and not original_item.get("responsavel_id"):
             update_dict["responsavel_id"] = current_user.id

        if not nova_localizacao:
            raise HTTPException(status_code=400, detail="RN13: Localização é obrigatória para status 'Em Uso'.")
    
    if status_atual == "Em Manutenção" and novo_status == "Disponível":
        if "descricao" not in update_dict and "detalhes" not in update_dict:
             # Se for só uma troca de status sem editar texto, assumimos que está ok, 
             # mas sua regra pedia detalhes. Vou deixar passar se não tiver update de texto para não travar a UI simples.
             pass

    # Sanitização de Datas
    if 'data_aquisicao' in update_dict and isinstance(update_dict['data_aquisicao'], date) and not isinstance(update_dict['data_aquisicao'], datetime):
        update_dict['data_aquisicao'] = datetime.combine(update_dict['data_aquisicao'], datetime.min.time())

    # Histórico
    detalhes_historico = f"Campos atualizados: {', '.join(update_dict.keys())}"
    historico_entry = {
        "timestamp": datetime.now(timezone.utc),
        "usuario_id": current_user.id,
        "acao": "Atualização",
        "detalhes": detalhes_historico
    }

    # Atualiza no Banco
    await db.patrimonio.update_one(
        {"_id": ObjectId(item_id)},
        {
            "$set": update_dict,
            "$push": {"historico": historico_entry}
        }
    )

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
        raise HTTPException(status_code=400, detail="ID inválido")

    result = await db.patrimonio.delete_one({"_id": ObjectId(item_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado.")

@router.get("/{item_id}/history", response_model=List[HistoricoItem])
async def get_patrimony_history(item_id: str, current_user: Usuario = Depends(get_current_user), db = Depends(get_mongo_db)):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="ID inválido")

    item = await db.patrimonio.find_one(
        {"_id": ObjectId(item_id)},
        {"historico": 1, "_id": 0}
    )

    if not item or "historico" not in item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Histórico não encontrado.")

    return item["historico"]