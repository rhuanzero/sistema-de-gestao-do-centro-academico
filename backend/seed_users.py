import asyncio
import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.sql_models import Usuario, Departamento, CargoEnum, StatusEnum

try:
    from app.security import get_password_hash
except ImportError:
    # Fallback apenas para teste caso a importação falhe fora do ambiente
    def get_password_hash(password):
        return f"hashed_{password}"

async def create_initial_users():
    print("--- Iniciando Script de Criação de Usuários ---")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Busca dos Departamentos
            dept_presidencia_row = await session.execute(select(Departamento).filter(Departamento.id == 1))
            dept_financeiro_row = await session.execute(select(Departamento).filter(Departamento.id == 2))
            dept_eventos_row = await session.execute(select(Departamento).filter(Departamento.id == 3))
            dept_comunicacao_row = await session.execute(select(Departamento).filter(Departamento.id == 4))
            dept_patrimonio_row = await session.execute(select(Departamento).filter(Departamento.id == 5))

            # Extração segura dos objetos (Row -> Model)
            dept_presidencia = dept_presidencia_row.scalar_one_or_none()
            dept_financeiro = dept_financeiro_row.scalar_one_or_none()
            dept_eventos = dept_eventos_row.scalar_one_or_none()
            dept_comunicacao = dept_comunicacao_row.scalar_one_or_none()
            dept_patrimonio = dept_patrimonio_row.scalar_one_or_none()

            # Verificação de segurança: Se os departamentos não existirem, abortar
            if not all([dept_presidencia, dept_financeiro, dept_eventos, dept_comunicacao, dept_patrimonio]):
                print("ERRO CRÍTICO: Um ou mais departamentos (IDs 1-5) não foram encontrados no banco.")
                print("Execute o seed de departamentos antes de criar usuários.")
                return

            # 2. Instanciação dos Usuários
            # Presidente
            user_presidente = Usuario(
                nome="Thauan",
                email="admin@calove.br",
                senha_hash=get_password_hash("123456"),
                cpf="000.000.001-91",
                telefone="21999999999",
                cargo=CargoEnum.Presidente,
                status=StatusEnum.Ativo,
                departamento=dept_presidencia, 
                centro_academico_id=1
            )

            # Membro de Eventos
            user_rhuan = Usuario(
                nome="Rhuan",
                email="rhuan@calove.br",
                senha_hash=get_password_hash("123456"),
                cpf="497.560.310-18",
                telefone="9837556851",
                cargo=CargoEnum.Membro,
                status=StatusEnum.Ativo,
                departamento=dept_eventos,
                centro_academico_id=1
            )

            # Tesoureiro (Financeiro)
            user_tesoureiro = Usuario(
                nome="Bruno",
                email="bruno@calove.br",
                senha_hash=get_password_hash("123456"),
                cpf="092.997.670-33",
                telefone="3534925391",
                cargo=CargoEnum.Tesoureiro,
                status=StatusEnum.Ativo,
                departamento=dept_financeiro,
                centro_academico_id=1
            )

            # Membro de Comunicação
            user_comunicacao = Usuario(
                nome="Thais",
                email="thais@calove.br",
                senha_hash=get_password_hash("123456"),
                cpf="123.456.789-00",
                telefone="21987654321",
                cargo=CargoEnum.Coordenador,
                status=StatusEnum.Ativo,
                departamento=dept_comunicacao,
                centro_academico_id=1
            )

            # Outro membro de Eventos (Dyego)
            user_eventos_dyego = Usuario(
                nome="Dyego",
                email="dyego@calove.br",
                senha_hash=get_password_hash("123456"),
                cpf="987.654.321-00",
                telefone="21912345678",
                cargo=CargoEnum.Membro,
                status=StatusEnum.Ativo,
                departamento=dept_eventos, # Reutiliza o objeto dept_eventos
                centro_academico_id=1
            )

            # Burocrático (Patrimônio)
            user_burocratico = Usuario(
                nome="Daniel",
                email="daniel@calove.br",
                senha_hash=get_password_hash("123456"),
                cpf="111.222.333-44",
                telefone="21998765432",
                cargo=CargoEnum.Membro,
                status=StatusEnum.Ativo,
                departamento=dept_patrimonio,
                centro_academico_id=1
            )

            # 3. Persistência
            session.add_all([
                user_presidente, 
                user_tesoureiro, 
                user_rhuan, 
                user_comunicacao, 
                user_eventos_dyego, 
                user_burocratico
            ])
            
            await session.commit()

            for user in [user_presidente, user_tesoureiro, user_rhuan, user_comunicacao, user_eventos_dyego, user_burocratico]:
                await session.refresh(user)

            print("SUCESSO: Todos os usuários criados!")
            print(f"Presidente: {user_presidente.nome} ({user_presidente.email}) - Dept: {user_presidente.departamento.nome if user_presidente.departamento else 'N/A'}")
            print(f"Tesoureiro: {user_tesoureiro.nome} ({user_tesoureiro.email})")
            print(f"Rhuan: {user_rhuan.nome} ({user_rhuan.email})")
            print(f"Comunicação: {user_comunicacao.nome} ({user_comunicacao.email})")
            print(f"Eventos (Dyego): {user_eventos_dyego.nome} ({user_eventos_dyego.email})")
            print(f"Burocracia: {user_burocratico.nome} ({user_burocratico.email})")

        except Exception as e:
            print(f"ERRO: Ocorreu um problema ao criar o usuário: {e}")
            await session.rollback()
            raise
        finally:
            pass

if __name__ == "__main__":
    asyncio.run(create_initial_users())