import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_criar_listar_produto(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    produto = {
        "nome": "Mouse Gamer",
        "descricao": "Mouse RGB",
        "preco": 120.0,
        "quantidade": 10,
    }
    response = client.post("/produtos", json=produto, headers=headers)
    assert response.status_code in (200, 201)
