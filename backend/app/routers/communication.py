from fastapi import APIRouter, Depends, HTTPException, Body, status
from bson import ObjectId
from app.database import get_mongo_db
from app.models.schemas import (
    PostagemCreate, PostagemUpdate, PostagemResponse,
    SolicitacaoComunicacaoCreate, SolicitacaoComunicacaoUpdate, SolicitacaoComunicacaoResponse,
    CreatedWithStatus, CreatedResponse, SimpleMessageResponse
)
from app.security import get_current_user
from app.models.sql_models import Usuario, CargoEnum
from typing import Optional, List
from datetime import datetime, timezone, date

router = APIRouter(prefix="/communication", tags=["Comunicação"])

# --- POSTAGENS ---

@router.post("/create_posts", response_model=CreatedWithStatus)
async def create_post(
    post: PostagemCreate,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    if current_user.cargo not in [CargoEnum.Coordenador, CargoEnum.Presidente]:
         raise HTTPException(status_code=403, detail="Permissão negada.")

    post_dict = post.model_dump()
    post_dict["autor_id"] = current_user.id
    post_dict["status"] = "Rascunho"
    post_dict["criado_em"] = datetime.now(timezone.utc)

    new_post = await db.comunicacao.insert_one(post_dict)
    return {"id": str(new_post.inserted_id), "status": "Rascunho"}

@router.put("/posts/{post_id}", response_model=SimpleMessageResponse)
async def update_post(
    post_id: str,
    update_data: PostagemUpdate,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    if current_user.cargo not in [CargoEnum.Coordenador, CargoEnum.Presidente]:
         raise HTTPException(status_code=403, detail="Permissão negada.")
    
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="ID inválido.")

    # Remove campos vazios para não apagar dados sem querer
    update_dict = {k: v for k, v in update_data.model_dump(exclude_unset=True).items()}
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="Nada para atualizar.")

    result = await db.comunicacao.update_one(
        {"_id": ObjectId(post_id)}, 
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Postagem não encontrada.")

    return {"message": "Postagem atualizada com sucesso."}

@router.get("/posts", response_model=List[PostagemResponse])
async def list_posts(db = Depends(get_mongo_db)):
    posts = await db.comunicacao.find().sort("data_agendamento", -1).to_list(length=100)
    results = []
    for post in posts:
        post["id"] = str(post["_id"])
        del post["_id"]
        results.append(post)
    return results

@router.delete("/posts/{post_id}", status_code=204)
async def delete_post(
    post_id: str,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    if current_user.cargo not in [CargoEnum.Coordenador, CargoEnum.Presidente]:
         raise HTTPException(status_code=403, detail="Permissão negada.")
    
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="ID inválido.")

    result = await db.comunicacao.delete_one({"_id": ObjectId(post_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Postagem não encontrada.")

# --- SOLICITAÇÕES / DOCS ---

@router.post("/requests", response_model=CreatedResponse)
async def create_request(
    solicitacao: SolicitacaoComunicacaoCreate,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    req_dict = solicitacao.model_dump()
    req_dict.update({
        "solicitante_id": current_user.id,
        "solicitante_nome": current_user.nome,
        "data_solicitacao": datetime.now(timezone.utc),
        "status": "Pendente"
    })
    
    if isinstance(req_dict.get("prazo_sugerido"), date) and not isinstance(req_dict.get("prazo_sugerido"), datetime):
        req_dict["prazo_sugerido"] = datetime.combine(req_dict["prazo_sugerido"], datetime.min.time())

    result = await db.solicitacoes_comunicacao.insert_one(req_dict)
    return {"id": str(result.inserted_id), "message": "Solicitação criada."}

@router.put("/requests/{req_id}", response_model=SimpleMessageResponse)
async def update_request(
    req_id: str,
    update_data: SolicitacaoComunicacaoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    if current_user.cargo not in [CargoEnum.Coordenador, CargoEnum.Presidente]:
         raise HTTPException(status_code=403, detail="Permissão negada.")

    if not ObjectId.is_valid(req_id):
        raise HTTPException(status_code=400, detail="ID inválido.")

    dados = {k: v for k, v in update_data.model_dump(exclude_unset=True).items()}
    
    if dados.get("prazo_sugerido") and isinstance(dados["prazo_sugerido"], date):
         dados["prazo_sugerido"] = datetime.combine(dados["prazo_sugerido"], datetime.min.time())

    result = await db.solicitacoes_comunicacao.update_one(
        {"_id": ObjectId(req_id)}, 
        {"$set": dados}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")

    return {"message": "Solicitação atualizada."}

@router.get("/requests", response_model=List[SolicitacaoComunicacaoResponse])
async def list_requests(db = Depends(get_mongo_db)):
    docs = await db.solicitacoes_comunicacao.find().sort("data_solicitacao", -1).to_list(length=100)
    results = []
    for d in docs:
        d["id"] = str(d["_id"])
        if isinstance(d.get("prazo_sugerido"), date) and not isinstance(d.get("prazo_sugerido"), datetime):
            d["prazo_sugerido"] = datetime.combine(d["prazo_sugerido"], datetime.min.time())
        results.append(d)
    return results