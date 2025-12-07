from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base
import os
from app.routers import auth, members, finance, events, communication, patrimony
from fastapi.middleware.cors import CORSMiddleware

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
    allow_origins=origins,
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

@app.get("/")
@app.get("/", response_model=dict)
def read_root():
    return {"message": "SGCA API Online. Acesse /docs para documentação."}