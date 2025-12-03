from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.routers import auth, members, finance, events, communication

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria tabelas MySQL na inicialização (se não existirem)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="SGCA API - Sistema de Gestão de Centro Acadêmico",
    description="API baseada no documento de ES1 para gestão financeira, eventos e membros.",
    version="1.0.0",
    lifespan=lifespan
)

# Incluindo Rotas
app.include_router(auth.router)
app.include_router(members.router)
app.include_router(finance.router)
app.include_router(events.router)
app.include_router(communication.router)

@app.get("/")
def read_root():
    return {"message": "SGCA API Online. Acesse /docs para documentação."}