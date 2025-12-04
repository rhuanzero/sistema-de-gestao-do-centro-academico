from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, date, timezone
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
    # Verificação de Permissão
    if current_user.cargo not in [CargoEnum.Presidente, CargoEnum.Coordenador]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    # REGRA DE UNICIDADE: Verifica se já existe um item com esse nome
    # Utilizamos busca case-insensitive para evitar "Cadeira" e "cadeira"
    existing_item = await db.patrimonio.find_one({"nome": {"$regex": f"^{item.nome}$", "$options": "i"}})
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"Já existe um item de patrimônio cadastrado com o nome '{item.nome}'."
        )

    item_dict = item.model_dump()
    
    # Converte date para datetime para ser compatível com BSON/MongoDB
    if isinstance(item_dict.get("data_aquisicao"), date) and not isinstance(item_dict.get("data_aquisicao"), datetime):
        item_dict["data_aquisicao"] = datetime.combine(item_dict["data_aquisicao"], datetime.min.time())

    # Adiciona o registro inicial ao histórico
    item_dict["historico"] = [{
        "timestamp": datetime.now(timezone.utc),
        "usuario_id": current_user.id,
        "acao": "Criação",
        "detalhes": f"Item criado por {current_user.nome}."
    }]

    result = await db.patrimonio.insert_one(item_dict)
    
    created_item = await db.patrimonio.find_one({"_id": result.inserted_id})
    created_item["id"] = str(created_item["_id"])
    return created_item

@router.get("/", response_model=List[PatrimonioResponse])
async def list_patrimony_items(current_user: Usuario = Depends(get_current_user),db = Depends(get_mongo_db)):
    items = []
    cursor = db.patrimonio.find()
    async for item in cursor:
        item["id"] = str(item["_id"])
        items.append(item)
    return items

@router.get("/{item_nome}", response_model=PatrimonioResponse)
async def get_patrimony_item(item_nome: str, current_user: Usuario = Depends(get_current_user), db = Depends(get_mongo_db)):
    # Busca exata pelo nome (ou use regex se quiser case-insensitive na URL também)
    item = await db.patrimonio.find_one({"nome": item_nome})
    
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item '{item_nome}' não encontrado.")
    
    item["id"] = str(item["_id"])
    return item
@router.put("/{item_nome}", response_model=PatrimonioResponse)
async def update_patrimony_item(
    item_nome: str,
    update_data: PatrimonioUpdate,
    db = Depends(get_mongo_db),
    current_user: Usuario = Depends(get_current_user)
):
    # RF16: Permissões de Edição
    if current_user.cargo not in [CargoEnum.Presidente, CargoEnum.Coordenador, CargoEnum.Membro]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    # Busca item original
    original_item = await db.patrimonio.find_one({"nome": item_nome})
    if not original_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item '{item_nome}' não encontrado.")

    update_dict = {k: v for k, v in update_data.model_dump(exclude_unset=True).items()}

    if not update_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum dado para atualizar.")

    # REGRA DE UNICIDADE NA ATUALIZAÇÃO
    if "nome" in update_dict and update_dict["nome"] != item_nome:
        novo_nome = update_dict["nome"]
        conflict_item = await db.patrimonio.find_one({"nome": {"$regex": f"^{novo_nome}$", "$options": "i"}})
        if conflict_item:
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=f"Não é possível renomear. Já existe um item com o nome '{novo_nome}'."
            )
            
    # --- VALIDAÇÃO RIGOROSA DAS REGRAS DE NEGÓCIO ---
    
    novo_status = update_dict.get("status")
    status_atual = original_item.get("status")
    
    # RN13: Status "Em Uso" exige Localização E Membro Responsável
    if novo_status == "Em Uso":
        # Validação de Localização
        nova_localizacao = update_dict.get("localizacao") or original_item.get("localizacao")
        # Validação de Responsável (Membro)
        # Nota: Estamos assumindo que o campo no Mongo é 'responsavel_id' ou 'usuario_id'
        # Se o usuário não enviou um responsável, assumimos que quem está atualizando (current_user) é o responsável?
        # Pela regra estrita "se um membro... for informado", devemos exigir o dado ou vincular o current_user explicitamente.
        novo_responsavel = update_dict.get("responsavel_id") or original_item.get("responsavel_id")

        if not nova_localizacao:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RN13: Para alterar status para 'Em Uso', a localização é obrigatória."
            )
        
        # Se não houver responsável vinculado, vinculamos automaticamente o usuário atual ou exigimos o campo
        if not novo_responsavel:
             # Opção A: Auto-atribuir (mais fluido)
             update_dict["responsavel_id"] = current_user.id
             # Opção B (Mais estrita): raise HTTPException se quiser forçar o envio manual
    
    # RN14: De "Em Manutenção" para "Disponível" exige registro
    if status_atual == "Em Manutenção" and novo_status == "Disponível":
        # Verifica se há uma descrição do reparo ou data explícita
        if "descricao" not in update_dict and "detalhes" not in update_dict:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RN14: Para finalizar a manutenção, é necessário informar os detalhes/conclusão do reparo."
            )

    # -------------------------------------------------------

    # Sanitização de Datas
    if 'data_aquisicao' in update_dict and isinstance(update_dict['data_aquisicao'], date) and not isinstance(update_dict['data_aquisicao'], datetime):
        update_dict['data_aquisicao'] = datetime.combine(update_dict['data_aquisicao'], datetime.min.time())

    # Montagem do Histórico
    detalhes_historico = f"Campos atualizados: {', '.join(update_dict.keys())}"
    
    if status_atual == "Em Manutenção" and novo_status == "Disponível":
        detalhes_historico += ". Manutenção registrada e concluída."

    historico_entry = {
        "timestamp": datetime.now(timezone.utc),
        "usuario_id": current_user.id,
        "acao": "Atualização",
        "detalhes": detalhes_historico
    }

    result = await db.patrimonio.update_one(
        {"nome": item_nome},
        {
            "$set": update_dict,
            "$push": {"historico": historico_entry}
        }
    )

    final_query_name = update_dict.get("nome", item_nome)
    updated_item = await db.patrimonio.find_one({"nome": final_query_name})
    
    updated_item["id"] = str(updated_item["_id"])
    return updated_item


@router.delete("/{item_nome}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patrimony_item(
    item_nome: str,
    db = Depends(get_mongo_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.cargo not in [CargoEnum.Presidente, CargoEnum.Coordenador]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    result = await db.patrimonio.delete_one({"nome": item_nome})

    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item '{item_nome}' não encontrado.")

@router.get("/{item_nome}/history", response_model=List[HistoricoItem])
async def get_patrimony_history(item_nome: str, current_user: Usuario = Depends(get_current_user), db = Depends(get_mongo_db)):
    item = await db.patrimonio.find_one(
        {"nome": item_nome},
        {"historico": 1, "_id": 0}
    )

    if not item or "historico" not in item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Histórico não encontrado para o item '{item_nome}'.")

    return item["historico"]