import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

@pytest.fixture
def admin_token():
    cadastro = {
    "nome": "Admin Teste",
    "email": "admin@teste.com",
    "cpf": "12345678901",
    "password": "admin123",
    "confirm_password": "admin123",
    "cod_confirmacao_email": "Confirmado",
    "data_nascimento": "1990-01-01",
    "cep": "12345-678",
    "complemento": "Casa"
}
    res_cadastro = client.post("/admins/cadastrar", json=cadastro)
    print("Cadastro admin:", res_cadastro.json())


    login = {
        "email": "admin@teste.com",
        "password": "admin123"
    }
    response = client.post("/admins/logar", json=login)
    print(response.json())
    assert response.status_code == 200
    assert "access_token" in response.json()
    return response.json()["access_token"]

def test_rota_protegida_com_token(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/admins/autenticar", headers=headers)
    assert response.status_code == 200
    assert response.json()["admin"]["email"] == "admin@teste.com"

def test_rota_protegida_sem_token():
    response = client.get("/admins/autenticar")  # Sem token
    assert response.status_code == 401
