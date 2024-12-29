from sqlmodel import create_engine, SQLModel
from decouple import config

def get_engine():
  return create_engine('sqlite:///buy-tech.db')

# Cria o Banco
def init_db():
  SQLModel.metadata.create_all(get_engine())