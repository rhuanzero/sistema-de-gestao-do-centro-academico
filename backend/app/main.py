from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base
import os
from app.routers import auth, members, finance, events, communication, patrimony
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users
from pydantic import BaseModel
from typing import List, Optional

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria tabelas MySQL na inicialização (se não existirem)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="SGCA API - Sistema de Gestão de Centro Acadêmico",
    description="API para gestão do centro academico.",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    "http://localhost:4200", # Endereço do Angular
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluindo Rotas
app.include_router(auth.router)
app.include_router(members.router)
app.include_router(finance.router)
app.include_router(events.router)
app.include_router(communication.router)
app.include_router(patrimony.router)
app.include_router(users.router)

@app.get("/")
@app.get("/", response_model=dict)
def read_root():
    return {"message": "SGCA API Online. Acesse /docs para documentação."}

# --- MODELOS DE DADOS (Pydantic) ---
# Têm que bater com as interfaces do Angular
class Postagem(BaseModel):
    id: Optional[int] = None
    titulo: str
    midia_destino: str
    data_agendamento: str
    status: str
    conteudo: Optional[str] = ""

class Solicitacao(BaseModel):
    id: Optional[int] = None
    titulo: str
    solicitante_nome: str
    prazo_sugerido: str
    status: str
    conteudo: Optional[str] = ""

# --- BANCO DE DADOS EM MEMÓRIA (Simulação) ---
# Se reiniciar o servidor, apaga tudo. Para persistir, precisaria de SQL.
db_posts: List[Postagem] = [
    Postagem(id=1, titulo="Post Exemplo Back", midia_destino="Instagram", data_agendamento="2025-12-25T10:00", status="Agendado", conteudo="Teste")
]
db_docs: List[Solicitacao] = []

# --- ROTAS PARA POSTAGENS ---

@app.get("/postagens", response_model=List[Postagem])
def listar_postagens():
    return db_posts

@app.post("/postagens", response_model=Postagem)
def criar_postagem(post: Postagem):
    post.id = len(db_posts) + 1  # Gera ID simples
    db_posts.append(post)
    return post

@app.put("/postagens/{post_id}", response_model=Postagem)
def atualizar_postagem(post_id: int, post_atualizado: Postagem):
    for index, post in enumerate(db_posts):
        if post.id == post_id:
            post_atualizado.id = post_id # Garante o ID
            db_posts[index] = post_atualizado
            return post_atualizado
    raise HTTPException(status_code=404, detail="Postagem não encontrada")

@app.delete("/postagens/{post_id}")
def deletar_postagem(post_id: int):
    for index, post in enumerate(db_posts):
        if post.id == post_id:
            del db_posts[index]
            return {"message": "Deletado com sucesso"}
    raise HTTPException(status_code=404, detail="Postagem não encontrada")

# --- ROTAS PARA SOLICITAÇÕES ---

@app.get("/solicitacoes", response_model=List[Solicitacao])
def listar_solicitacoes():
    return db_docs

@app.post("/solicitacoes", response_model=Solicitacao)
def criar_solicitacao(doc: Solicitacao):
    doc.id = len(db_docs) + 1
    db_docs.append(doc)
    return doc

@app.put("/solicitacoes/{doc_id}", response_model=Solicitacao)
def atualizar_solicitacao(doc_id: int, doc_atualizado: Solicitacao):
    for index, doc in enumerate(db_docs):
        if doc.id == doc_id:
            doc_atualizado.id = doc_id
            db_docs[index] = doc_atualizado
            return doc_atualizado
    raise HTTPException(status_code=404, detail="Solicitação não encontrada")

@app.delete("/solicitacoes/{doc_id}")
def deletar_solicitacao(doc_id: int):
    for index, doc in enumerate(db_docs):
        if doc.id == doc_id:
            del db_docs[index]
            return {"message": "Deletado com sucesso"}
    raise HTTPException(status_code=404, detail="Solicitação não encontrada")