from fastapi import APIRouter, Depends, HTTPException
from app.database import get_mongo_db
from app.models.schemas import PostagemCreate
from app.security import get_current_user
from app.models.sql_models import Usuario, CargoEnum

router = APIRouter(prefix="/posts", tags=["Comunicação e Burocrático"])

@router.post("/")
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