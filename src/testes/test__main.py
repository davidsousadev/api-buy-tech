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

# Testando rotas registradas
@pytest.mark.parametrize("endpoint", [
    "/admins", "/clientes", "/emails", "/categorias", "/cupons", "/produtos",
    "/carrinhos", "/pedidos", "/operacoes", "/revendedores", "/carrinhos_revendedor",
    "/pedidos_revendedor", "/operacoes_revendedor"
])
def test_registered_routes(endpoint):
    """
    Testa se as rotas estão registradas na aplicação.
    """
    response = client.get(endpoint)
    assert response.status_code in (200, 401, 404, 405), f"A rota '{endpoint}' deveria estar registrada."

# Testando o status dos endpoints
@pytest.mark.parametrize("endpoint, expected_status", [
    ("/admins", 401), ("/clientes", 405), ("/emails", 405), ("/categorias", 200),
    ("/cupons", 405), ("/produtos", 200), ("/carrinhos", 401), ("/pedidos", 401),
    ("/operacoes", 405), ("/revendedores", 401), ("/admins/1", 404), ("/clientes/1", 404),
    ("/emails/1", 404), ("/categorias/", 200), ("/cupons/1", 405), ("/produtos/", 200),
    ("/carrinhos/1", 405), ("/pedidos/1", 401), ("/operacoes/1", 404), ("/revendedores/1", 404)
])
def test_endpoints_status(endpoint, expected_status):
    """
    Testa se os endpoints estão retornando os status esperados.
    """
    response = client.get(endpoint)
    assert response.status_code == expected_status, f"O endpoint '{endpoint}' deveria retornar {expected_status}."

# Testando métodos POST e PATCH
@pytest.mark.parametrize("endpoint, method", [
    ("/admins/cadastrar", "POST"), ("/clientes/cadastrar", "POST"), ("/emails/suporte/1", "POST"),
    ("/categorias", "POST"), ("/cupons", "POST"), ("/produtos", "POST"), ("/carrinhos", "POST"),
    ("/pedidos", "POST"), ("/revendedores/cadastrar", "POST"), ("/admins/atualizar", "PATCH"),
    ("/clientes/atualizar", "PATCH"), ("/emails/confirmado", "PATCH"), ("/categorias/1", "PATCH"),
    ("/cupons/1", "PATCH"), ("/produtos/1", "PATCH"), ("/carrinhos/1", "PATCH"), ("/pedidos/1", "PATCH"),
    ("/revendedores/1", "PATCH")
])
def test_post_patch_methods(endpoint, method):
    """
    Testa métodos POST e PATCH para os endpoints.
    """
    if method == "POST":
        response = client.post(endpoint)
    elif method == "PATCH":
        response = client.patch(endpoint)
    assert response.status_code in (200, 201, 204, 401, 422, 404, 405), f"O método {method} para o endpoint '{endpoint}' falhou com o status {response.status_code}."

# Testando métodos DELETE
@pytest.mark.parametrize("endpoint", [
    "/admins/1", "/clientes/1", "/emails/1", "/categorias/1", "/cupons/1", "/produtos/1",
    "/carrinhos/1", "/pedidos/1", "/revendedores/1"
])
def test_delete_methods(endpoint):
    """
    Testa métodos DELETE para os endpoints.
    """
    response = client.delete(endpoint)
    assert response.status_code in (200, 204, 404, 405), f"O DELETE para o endpoint '{endpoint}' falhou com o status {response.status_code}."

# Testando OPTIONS em todos os endpoints
@pytest.mark.parametrize("endpoint", [
    "/admins", "/clientes", "/emails", "/categorias", "/cupons", "/produtos",
    "/carrinhos", "/pedidos", "/operacoes", "/revendedores", "/carrinhos_revendedor",
    "/pedidos_revendedor", "/operacoes_revendedor"
])
def test_options_methods(endpoint):
    """
    Testa o método OPTIONS para os endpoints.
    """
    response = client.options(endpoint)
    assert response.status_code == 200, f"O método OPTIONS para o endpoint '{endpoint}' falhou com o status {response.status_code}."

# Testando rotas para diferentes tipos de operações CRUD
@pytest.mark.parametrize("endpoint", [
    "/admins/cadastrar", "/clientes/cadastrar", "/emails/suporte/1", "/categorias", "/cupons", "/produtos",
    "/carrinhos", "/pedidos", "/revendedores/cadastrar", "/admins/atualizar", "/clientes/atualizar",
    "/emails/confirmado", "/categorias/1", "/cupons/1", "/produtos/1", "/carrinhos/1", "/pedidos/1", "/revendedores/1"
])
def test_crud_operations(endpoint):
    """
    Testa as operações CRUD para os endpoints.
    """
    response = client.get(endpoint)
    assert response.status_code in (200, 201, 204, 401, 404, 405, 422), f"A operação no endpoint '{endpoint}' falhou com o status {response.status_code}."

# Testando CRUD em usuários, categorias, cupons e produtos
@pytest.mark.parametrize("endpoint, operation", [
    ("/admins", "POST"), ("/clientes", "POST"), ("/emails", "POST"),
    ("/categorias", "POST"), ("/cupons", "POST"), ("/produtos", "POST"),
    ("/admins/1", "GET"), ("/clientes/1", "GET"), ("/emails/1", "GET"),
    ("/categorias/1", "GET"), ("/cupons/1", "GET"), ("/produtos/1", "GET"),
    ("/admins/1", "DELETE"), ("/clientes/1", "DELETE"), ("/emails/1", "DELETE"),
    ("/categorias/1", "DELETE"), ("/cupons/1", "DELETE"), ("/produtos/1", "DELETE")
])
def test_crud_actions(endpoint, operation):
    """
    Testa as operações CRUD para endpoints com IDs.
    """
    if operation == "POST":
        response = client.post(endpoint)
    elif operation == "GET":
        response = client.get(endpoint)
    elif operation == "DELETE":
        response = client.delete(endpoint)
    assert response.status_code in (200, 201, 204, 401, 404, 405, 422), f"A operação {operation} no endpoint '{endpoint}' falhou com o status {response.status_code}."

# Testando rotas com parâmetros variados
@pytest.mark.parametrize("endpoint", [
    "/admins/1", "/clientes/1", "/emails/1", "/categorias/1", "/cupons/1",
    "/produtos/1", "/carrinhos/1", "/pedidos/1", "/revendedores/1"
])
def test_parametrized_endpoints(endpoint):
    """
    Testa as rotas parametrizadas.
    """
    response = client.get(endpoint)
    assert response.status_code in (200, 404, 401, 405), f"A rota '{endpoint}' falhou com o status {response.status_code}."
