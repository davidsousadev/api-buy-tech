from sqlmodel import create_engine, SQLModel
from decouple import config

DATABASE_URL = config("DATABASE_URL", default="sqlite:///buy-tech.db")

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
