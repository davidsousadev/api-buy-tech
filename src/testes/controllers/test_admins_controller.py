import pytest
from starlette.testclient import TestClient
from unittest.mock import patch
from faker import Faker
import uuid

from sqlmodel import Session
from src.main import app
from src.models.admins_models import Admin
from src.database import get_engine
from src.auth_utils import hash_password

fake = Faker()

from datetime import datetime, timedelta
import jwt
from src.auth_utils import SECRET_KEY, ALGORITHM, ACCESS_EXPIRES

@pytest.fixture
def token_admin(create_admin):
    expire = datetime.utcnow() + timedelta(minutes=30)  # expira em 30 minutos
    payload = {
        "sub": create_admin["email"],
        "exp": int(expire.timestamp())  # timestamp Unix como inteiro
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def criar_token_acesso(dados: dict):
    to_encode = dados.copy()
    # Convertendo ACCESS_EXPIRES (segundos) para timedelta
    expire = datetime.utcnow() + timedelta(seconds=ACCESS_EXPIRES)
    to_encode.update({"exp": int(expire.timestamp())})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

# ---------- FIXTURES ----------

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def admin_data():
    return {
        "nome": "Admin Teste",
        "email": f"{uuid.uuid4().hex[:6]}@teste.com",
        "cpf": fake.ssn(),
        "password": "admin123",
        "confirm_password": "admin123",
        "data_nascimento": "1990-01-01",
        "telefone": "11999999999",
        "cep": 12345678,
        "complemento": "Casa"
    }

@pytest.fixture
def create_admin(admin_data):
    admin = Admin(
        nome=admin_data["nome"],
        email=admin_data["email"],
        cpf=admin_data["cpf"],
        cod_confirmacao_email="Confirmado",
        password=hash_password(admin_data["password"]),
        data_nascimento=admin_data["data_nascimento"],
        telefone=admin_data["telefone"],
        cep=admin_data["cep"],
        complemento=admin_data["complemento"],
        status=True,
        admin=True
    )
    with Session(get_engine()) as session:
        session.add(admin)
        session.commit()
        session.refresh(admin)
    return admin_data

@pytest.fixture
def token_admin(create_admin):
    return criar_token_acesso({"sub": create_admin["email"]})

# ---------- TESTES OPTIONS ----------

def test_options_admins(client):
    response = client.options("/admins")
    assert response.status_code == 200
    assert response.json() == {"methods": ["GET", "POST", "PATCH"]}

# ---------- TESTES GET /admins ----------

def test_listar_admins_com_token(client, token_admin):
    headers = {"Authorization": f"Bearer {token_admin}"}
    response = client.get("/admins", headers=headers)

    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)

def test_listar_admins_token_invalido(client):
    headers = {"Authorization": "Bearer token_falso"}
    response = client.get("/admins", headers=headers)
    assert response.status_code == 200  # Alterar na pós produção para 401

# ---------- TESTES POST /admins/cadastrar ----------

@patch("src.controllers.admins_controller.enviar_email", return_value=True)
def test_cadastro_admin_sucesso(mock_enviar_email, client, admin_data):
    response = client.post("/admins/cadastrar", json=admin_data)
    assert response.status_code == 201
    assert response.json()["detail"] is True
    assert "message" in response.json()

@patch("src.controllers.admins_controller.enviar_email", return_value=True)
def test_cadastro_email_existente(mock_enviar_email, client, create_admin):
    response = client.post("/admins/cadastrar", json=create_admin)
    assert response.status_code == 200
    assert "E-mail já cadastrado" in response.json()["detail"]

@patch("src.controllers.admins_controller.enviar_email", return_value=True)
def test_cadastro_cpf_existente(mock_enviar_email, client, create_admin):
    new_data = create_admin.copy()
    new_data["email"] = f"{uuid.uuid4().hex[:6]}@teste.com"
    response = client.post("/admins/cadastrar", json=new_data)
    assert response.status_code == 200
    assert "CPF já cadastrado" in response.json()["detail"]

def test_cadastro_senhas_diferentes(client, admin_data):
    admin_data["confirm_password"] = "senha_diferente"
    response = client.post("/admins/cadastrar", json=admin_data)
    assert response.status_code == 200
    assert "Senhas não coincidem" in response.json()["detail"]
