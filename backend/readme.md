# Utilizar o Python 3.11

# inicializar o ambiente - python -m venv .venv

# Escolher o ambiente - .venv\Scripts\activate

# Instalar as dependencias - pip install -r requirements.txt

# Caso o pip nao esteja instalado - python -m ensurepip --upgrade

# Definir o .env conforme suas credenciais

# Iniciar o servidor - uvicorn main:app --reload

# Após executar o script sql no documento, execute o seed_users.py com o ambiente selecionado para criar o presidente e os membros e ter acesso ao restante das rotas da api
email e senha do admin:
email - admin@sgca.com
senha - 123456 

Todos os usuarios tem a mesma senha, verifique no mysql os usuarios.

# python create_admin.py