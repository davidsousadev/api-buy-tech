from sqlmodel import create_engine, SQLModel
from decouple import config

def get_engine():
    """    
    # SQLite
    sqlite_url = 'sqlite:///buy-tech.db'
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    # print("Conectado ao SQLite local.")
    return engine


"""    
    # PostgreSQL
    try:
        user = config('DB_USERNAME')
        password = config('DB_PASSWORD')
        db_name = config('DB_NAME')
        host = config('DB_HOST')
        port = config('DB_PORT')
        postgres_url = f'postgresql://{user}:{password}@{host}:{port}/{db_name}?sslmode=require'
        engine = create_engine(postgres_url)
        engine.connect().close()
        # print("Conectado ao PostgreSQL com sucesso.")
        return engine
    except Exception as e:
        print(f"Falha ao conectar ao PostgreSQL: {e}")


        

"""
    # MySQL
    try:
        user = config('MYSQL_USERNAME', default=user)
        password = config('MYSQL_PASSWORD', default=password)
        db_name = config('MYSQL_DB_NAME', default=db_name)
        host = config('MYSQL_HOST', default=host)
        port = config('MYSQL_PORT', default='3306')
        mysql_url = f'mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}'
        engine = create_engine(mysql_url)
        engine.connect().close()
        print("Conectado ao MySQL com sucesso.")
        return engine
    except Exception as e:
        print(f"Falha ao conectar ao MySQL: {e}")
"""    

def init_db():
    engine = get_engine()
    try:
        SQLModel.metadata.create_all(engine)
        print("Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
    