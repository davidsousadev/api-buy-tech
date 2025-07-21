# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from src.main import app
from src.database import get_engine

# Banco de dados de teste SQLite (arquivo local)
TEST_DATABASE_URL = "sqlite:///./buy_tech_test.db"

# Cria engine para o banco de teste
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

# Override da dependência do banco para usar o engine de teste
app.dependency_overrides[get_engine] = lambda: test_engine

@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    # Cria todas as tabelas no banco de teste antes da sessão de testes
    SQLModel.metadata.create_all(test_engine)
    yield
    # Se quiser limpar tudo depois dos testes, descomente:
    # SQLModel.metadata.drop_all(test_engine)

@pytest.fixture(scope="function", autouse=True)
def clear_tables():
    # Limpa os dados das tabelas antes de cada teste para garantir isolamento
    with Session(test_engine) as session:
        for table in reversed(SQLModel.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()

@pytest.fixture()
def client():
    # TestClient usando o app com banco de teste
    return TestClient(app)

@pytest.fixture()
def test_engine_fixture():
    # Engine para acesso direto ao banco de teste (ex: sessões manuais)
    return test_engine

@pytest.fixture()
def session(test_engine_fixture):
    # Fixture que cria e fornece uma sessão do banco de dados para testes
    with Session(test_engine_fixture) as session:
        yield session
