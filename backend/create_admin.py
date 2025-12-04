import asyncio
import sys
import os

# Adiciona o diretório atual ao Python Path para conseguir importar o 'app'
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.database import AsyncSessionLocal, engine, Base
from app.models.sql_models import Usuario, Departamento, CargoEnum, StatusEnum, CentroAcademico
from app.security import get_password_hash

async def create_first_president():
    print("--- Iniciando Script de Criação do Administrador (Presidente) ---")
    
    # 1. Cria as tabelas se elas não existirem (garantia)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        try:
            # 2. Verificar se o CALOVE existe
            print("Verificando Centro Acadêmico CALOVE...")
            query_ca = select(CentroAcademico).where(CentroAcademico.id == 1)
            result_ca = await session.execute(query_ca)
            centro_academico = result_ca.scalars().first()

            if not centro_academico:
                print("ERRO: Centro Acadêmico com ID 1 (CALOVE) não encontrado.")
                return

            # 3. Verificar/Criar o Departamento 'Presidência' vinculado ao CALOVE
            print("Verificando departamento 'Presidência'...")
            query_dept = select(Departamento).where(
                (Departamento.nome == "Presidência") & 
                (Departamento.centro_academico_id == 1)
            )
            result_dept = await session.execute(query_dept)
            departamento = result_dept.scalars().first()

            if not departamento:
                departamento = Departamento(
                    nome="Presidência",
                    centro_academico_id=1
                )
                session.add(departamento)
                await session.commit()
                await session.refresh(departamento)
                print(f"Departamento 'Presidência' criado com ID: {departamento.id}")
            else:
                print(f"Departamento 'Presidência' já existe (ID: {departamento.id}).")

            # 4. Verificar se já existe o usuário Presidente
            email_admin = "admin@calove.br"
            query_user = select(Usuario).where(Usuario.email == email_admin)
            result_user = await session.execute(query_user)
            user = result_user.scalars().first()

            if user:
                print(f"ATENÇÃO: Usuário '{email_admin}' já existe. Nenhuma ação realizada.")
                return

            # 5. Criar o Presidente
            print(f"Criando usuário Presidente '{email_admin}'...")
            
            # Hash da senha (123456)
            senha_secreta = "123456"
            senha_hash = get_password_hash(senha_secreta)

            novo_presidente = Usuario(
                nome="Thauan",
                email=email_admin,
                senha_hash=senha_hash,
                cpf="000.000.001-91",  # CPF Fictício
                telefone="21999999999",
                cargo=CargoEnum.Presidente,
                status=StatusEnum.Ativo,
                departamento_id=departamento.id,
                centro_academico_id=1
            )

            session.add(novo_presidente)
            await session.commit()
            await session.refresh(novo_presidente)

            print("SUCESSO: Presidente criado!")
            print("------------------------------------------------")
            print(f"Login: {novo_presidente.email}")
            print(f"Senha: {senha_secreta}")
            print("------------------------------------------------")

        except Exception as e:
            print(f"ERRO: Ocorreu um problema ao criar o usuário: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

if __name__ == "__main__":
    asyncio.run(create_first_president())