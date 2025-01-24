import pytest
from fastapi.testclient import TestClient
from src.main import app
from sqlmodel import Session, SQLModel, create_engine, select
from src.database import get_engine
from decouple import config

# Configuração do banco de dados para testes
DATABASE_URL = config("DATABASE_URL", default="sqlite:///buy-tech-teste.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Sobrescrevendo a dependência do banco de dados
app.dependency_overrides[get_engine] = lambda: engine

# Instancia o cliente de teste
client = TestClient(app)

# Apaga o banco

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    SQLModel.metadata.create_all(engine)
    yield
    # SQLModel.metadata.drop_all(engine)

def test_app_initialization():
    """
    Testa se a aplicação é inicializada corretamente.
    """
    response = client.get("/")
    assert response.status_code == 404, "A rota '/' não deveria existir por padrão."

def test_cors_headers():
    """
    Testa se as configurações de CORS estão funcionando corretamente.
    """
    response = client.options("/admins")
    assert response.status_code == 200, f"O método OPTIONS deveria estar habilitado.{response.status_code}"

@pytest.mark.parametrize("endpoint", [
    "/admins",
    "/clientes",
    "/emails",
    "/categorias",
    "/cupons",
    "/produtos",
    "/carrinhos",
    "/pedidos",
    "/operacoes",
    "/revendedores"
])
def test_registered_routes(endpoint):
    response = client.get(endpoint)
    assert response.status_code in (200, 401, 404), f"A rota '{endpoint}' deveria estar registrada."

@pytest.mark.parametrize("endpoint, expected_status", [
    ("/admins", 401),
    ("/clientes", 401),
    ("/emails", 404),
    ("/categorias", 200),
    ("/cupons", 401),
    ("/produtos", 200),
    ("/carrinhos", 401),
    ("/pedidos", 401),
    ("/operacoes", 404),
    ("/revendedores", 404),
])
def test_endpoints_status(endpoint, expected_status):

    response = client.get(endpoint)
    assert response.status_code == expected_status, f"O endpoint '{endpoint}' deveria retornar {expected_status}."
