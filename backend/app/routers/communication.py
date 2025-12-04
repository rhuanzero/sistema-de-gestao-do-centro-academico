from fastapi import APIRouter, Depends, HTTPException, Body
from bson import ObjectId
from app.database import get_mongo_db
from app.models.schemas import PostagemCreate, SolicitacaoComunicacaoCreate
from app.security import get_current_user
from app.models.sql_models import Usuario, CargoEnum
from typing import Optional
router = APIRouter(prefix="/communication", tags=["Comunicação e Burocrático"])

@router.post("/create_posts")
async def create_post(
    post: PostagemCreate,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    # Apenas Coordenadores 
    if current_user.cargo != CargoEnum.Coordenador:
         raise HTTPException(status_code=403, detail="Permissão negada.")

    post_dict = post.model_dump()
    post_dict["autor_id"] = current_user.id
    post_dict["status"] = "Rascunho" # Padrão definido no UC07

    new_post = await db.comunicacao.insert_one(post_dict)
    return {"id": str(new_post.inserted_id), "status": "Rascunho"}

@router.put("/posts/{post_id}/status")
async def update_post_status(
    post_id: str,
    status: str = Body(..., embed=True),
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    if current_user.cargo != CargoEnum.Coordenador:
        raise HTTPException(status_code=403, detail="Apenas Coordenadores podem alterar o status de postagens.")

    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="ID de postagem inválido.")

    result = await db.comunicacao.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"status": status}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Postagem não encontrada.")

    return {"message": f"Status da postagem atualizado para '{status}'."}

@router.post("/requests", status_code= 201)
async def create_communication_request(
    solicitacao: SolicitacaoComunicacaoCreate,
    current_user: Usuario = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    solicitacao_dict = solicitacao.model_dump()
    solicitacao_dict.update({
        "solicitante_id": current_user.id,
        "solicitante_nome": current_user.nome,
        "data_solicitacao": datetime.utcnow(),
        "status": "Pendente"
    })

    # Converte date para datetime
    if isinstance(solicitacao_dict.get("prazo_sugerido"), date) and not isinstance(solicitacao_dict.get("prazo_sugerido"), datetime):
        solicitacao_dict["prazo_sugerido"] = datetime.combine(solicitacao_dict["prazo_sugerido"], datetime.min.time())

    result = await db.solicitacoes_comunicacao.insert_one(solicitacao_dict)
    return {"id": str(result.inserted_id), "message": "Solicitação de comunicação enviada com sucesso."}


    
@router.get("/posts")
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