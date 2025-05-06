from sqlmodel import create_engine, SQLModel
from decouple import config

DATABASE_URL = config("DATABASE_URL", default="sqlite:///buy-tech.db")

# Usuário e Senha
user = config('DB_USERNAME')
password = config('DB_PASSWORD')
# Nome do Banco de Dados
db_name = config('DB_NAME')
# Host e Porta
host = config('DB_HOST')
port = config('DB_PORT')
# Montar a URL para conexão
# DATABASE_URL = f'postgresql://{user}:{password}@{host}:{port}/{db_name}?sslmode=require'

def get_engine():
    connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    return create_engine(DATABASE_URL, connect_args=connect_args)

def init_db():
    try:
        engine = get_engine()
        SQLModel.metadata.create_all(engine)
        print("Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
