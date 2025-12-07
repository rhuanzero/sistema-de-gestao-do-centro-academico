from fastapi import APIRouter, Depends, HTTPException, Body
from bson import ObjectId
from app.database import get_mongo_db
from app.models.schemas import (
    PostagemCreate,
    PostagemUpdate,
    PostagemResponse,
    SolicitacaoComunicacaoCreate,
    SolicitacaoComunicacaoResponse,
    CreatedWithStatus,
    CreatedResponse,
    SimpleMessageResponse,
)
from app.security import get_current_user
from app.models.sql_models import Usuario, CargoEnum
from typing import Optional
from datetime import datetime, timezone, date

router = APIRouter(prefix="/communication", tags=["Comunicação e Burocrático"])

@router.post("/create_posts", response_model=CreatedWithStatus)
async def create_post(
    post: PostagemCreate,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    # Apenas Coordenadores e Presidente podem criar postagens
    if current_user.cargo != CargoEnum.Coordenador and current_user.cargo != CargoEnum.Presidente:
         raise HTTPException(status_code=403, detail="Permissão negada.")

    post_dict = post.model_dump()
    post_dict["autor_id"] = current_user.id
    post_dict["status"] = "Rascunho" # Padrão definido no UC07

    new_post = await db.comunicacao.insert_one(post_dict)
    return {"id": str(new_post.inserted_id), "status": "Rascunho"}


@router.put("/posts/{post_titulo}", response_model=PostagemResponse)
async def update_post(
    post_titulo: str,
    update_data: PostagemUpdate,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    if current_user.cargo not in [CargoEnum.Coordenador, CargoEnum.Presidente]:
         raise HTTPException(status_code=403, detail="Permissão negada.")

    post = await db.comunicacao.find_one({"titulo": {"$regex": f"^{post_titulo}$", "$options": "i"}})
    if not post:
        raise HTTPException(status_code=404, detail="Postagem não encontrada.")

    update_dict = {k: v for k, v in update_data.items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")

    result = await db.comunicacao.update_one({"_id": post["_id"]}, {"$set": update_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Falha ao atualizar a postagem.")

    updated = await db.comunicacao.find_one({"_id": post["_id"]})
    updated["id"] = str(updated["_id"])
    del updated["_id"]
    return updated


@router.delete("/posts/{post_titulo}", status_code=204)
async def delete_post(
    post_titulo: str,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    if current_user.cargo not in [CargoEnum.Coordenador, CargoEnum.Presidente]:
         raise HTTPException(status_code=403, detail="Permissão negada.")

    post = await db.comunicacao.find_one({"titulo": {"$regex": f"^{post_titulo}$", "$options": "i"}})
    if not post:
        raise HTTPException(status_code=404, detail="Postagem não encontrada.")

    result = await db.comunicacao.delete_one({"_id": post["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Falha ao deletar a postagem.")
    return

@router.put("/posts/{post_titulo}/status", response_model=SimpleMessageResponse)
async def update_post_status(
    post_titulo: str,
    status: str = Body(..., embed=True),
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    if current_user.cargo not in [CargoEnum.Coordenador, CargoEnum.Presidente]:
        raise HTTPException(
            status_code=403, 
            detail="Apenas Coordenadores ou o Presidente podem alterar o status de postagens."
        )

    # Busca a postagem pelo título (case-insensitive)
    post = await db.comunicacao.find_one({"titulo": {"$regex": f"^{post_titulo}$", "$options": "i"}})
    
    if not post:
        raise HTTPException(status_code=404, detail="Postagem não encontrada.")

    # Atualiza o status da postagem
    result = await db.comunicacao.update_one(
        {"_id": post["_id"]},
        {
            "$set": {
                "status": status,
                "atualizado_em": datetime.now(timezone.utc),
                "atualizado_por": {
                    "id": str(current_user.id),
                    "nome": current_user.nome,
                    "cargo": current_user.cargo.value
                }
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Falha ao atualizar a postagem.")

    return {"message": f"Status da postagem '{post_titulo}' atualizado para '{status}'."}

@router.post("/requests", status_code=201, response_model=CreatedResponse)
async def create_communication_request(
    solicitacao: SolicitacaoComunicacaoCreate,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    solicitacao_dict = solicitacao.model_dump()
    solicitacao_dict.update({
        "solicitante_id": current_user.id,
        "solicitante_nome": current_user.nome,
        "data_solicitacao": datetime.now(timezone.utc),
        "status": "Pendente"
    })

    # Converte date para datetime
    if isinstance(solicitacao_dict.get("prazo_sugerido"), date) and not isinstance(solicitacao_dict.get("prazo_sugerido"), datetime):
        solicitacao_dict["prazo_sugerido"] = datetime.combine(solicitacao_dict["prazo_sugerido"], datetime.min.time())

    result = await db.solicitacoes_comunicacao.insert_one(solicitacao_dict)
    return {"id": str(result.inserted_id), "message": "Solicitação de comunicação enviada com sucesso."}


@router.get("/requests", response_model=list[SolicitacaoComunicacaoResponse])
async def list_communication_requests(
    status: Optional[str] = None,
    db = Depends(get_mongo_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Apenas Coordenadores e Presidente podem listar solicitações
    if current_user.cargo not in [CargoEnum.Coordenador, CargoEnum.Presidente]:
        raise HTTPException(status_code=403, detail="Permissão negada.")

    query = {}
    if status:
        query["status"] = status

    docs = await db.solicitacoes_comunicacao.find(query).sort("data_solicitacao", -1).to_list(length=1000)

    results = []
    for d in docs:
        d["id"] = str(d["_id"])
        # garante que prazo_sugerido e data_solicitacao são datetimes
        if isinstance(d.get("prazo_sugerido"), date) and not isinstance(d.get("prazo_sugerido"), datetime):
            d["prazo_sugerido"] = datetime.combine(d["prazo_sugerido"], datetime.min.time())
        results.append({
            "id": d["id"],
            "titulo": d.get("titulo"),
            "descricao": d.get("descricao"),
            "prazo_sugerido": d.get("prazo_sugerido"),
            "publico_alvo": d.get("publico_alvo"),
            "solicitante_id": d.get("solicitante_id"),
            "solicitante_nome": d.get("solicitante_nome"),
            "data_solicitacao": d.get("data_solicitacao"),
            "status": d.get("status"),
        })

    return results


    
@router.get("/posts", response_model=list[PostagemResponse])
async def list_posts(
    status: Optional[str] = None,
    db = Depends(get_mongo_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista as postagens de comunicação.
    Permite filtrar pelo status (ex: 'Rascunho', 'Aprovado').
    Qualquer usuário autenticado pode visualizar (transparência da equipe),
    mas a edição é restrita a coordenadores.
    """
    
    # Monta a query de filtro baseada no parâmetro opcional
    query = {}
    if status:
        query["status"] = status
    
    # Busca na collection 'comunicacao' (mesma usada no create_post)
    # Limite de 100 para evitar sobrecarga
    posts = await db.comunicacao.find(query).to_list(length=100)
    
    # Processamento para serialização (Converter ObjectId para string)
    results = []
    for post in posts:
        post["id"] = str(post["_id"])
        del post["_id"]
        results.append(post)
        
    return results