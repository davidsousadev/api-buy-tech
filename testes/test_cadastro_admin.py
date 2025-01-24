import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from src.main import app

from src.models.admins_models import Admin
from src.models.clientes_models import Cliente
from src.database import get_engine
from decouple import config

# Configuração do banco de dados para testes
DATABASE_URL = config("DATABASE_URL", default="sqlite:///buy-tech-teste.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Sobrescrevendo a dependência do banco de dados
app.dependency_overrides[get_engine] = lambda: engine

# Apaga o banco
@pytest.fixture(scope="function", autouse=True)
def setup_database():
    SQLModel.metadata.create_all(engine)
    yield
    # SQLModel.metadata.drop_all(engine)



client = TestClient(app)


def test_cadastrar_admin_sucesso():
    admin_data = {
        "nome": "Admin Teste",
        "email": "davidk1k3k@gmail.com",
        "cpf": "12345678900",
        "data_nascimento": "1990-01-01",
        "telefone": "11999999999",
        "cep": "12345678",
        "complemento": "Apto 101",
        "password": "senha123",
        "confirm_password": "senha123",
    }
    response = client.post("/admins/cadastrar", json=admin_data)
    assert response.status_code == 200
    assert response.json() == {
        "message": "Administrador cadastrado com sucesso! E-mail de confirmação enviado."
    }

    with Session(engine) as session:
        admin = session.exec(select(Admin).where(Admin.email == admin_data["email"])).first()
        assert admin is not None
        assert admin.nome == admin_data["nome"]


def test_email_ja_cadastrado_como_admin():
    admin_data = {
        "nome": "Admin Teste",
        "email": "davidk1k3k@gmail.com",
        "cpf": "12345678900",
        "data_nascimento": "1990-01-01",
        "telefone": "11999999999",
        "cep": "12345678",
        "complemento": "Apto 101",
        "password": "senha123",
        "confirm_password": "senha123",
    }
    client.post("/admins/cadastrar", json=admin_data)
    response = client.post("/admins/cadastrar", json=admin_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Já existe um administrador com esse email"


def test_email_ja_cadastrado_como_cliente():
    with Session(engine) as session:
        cliente_data = Cliente(
            nome="Cliente Teste",
            email="davidk1k3k@gmail.com",
            cod_confirmacao_email="123456",
            cpf="12345678901",
            data_nascimento="1995-01-01",
            telefone="11988888888",
            cep="12345678",
            complemento="Casa",
            password="senha123",
            pontos_fidelidade=0,
            clube_fidelidade=False,
            cod_indicacao=0,
            status=True
        )
        session.add(cliente_data)
        session.commit()

    admin_data = {
        "nome": "Admin Teste",
        "email": "davidk1k3k@gmail.com",
        "cpf": "98765432100",
        "data_nascimento": "1990-01-01",
        "telefone": "11999999999",
        "cep": "12345678",
        "complemento": "Apto 101",
        "password": "senha123",
        "confirm_password": "senha123",
    }
    response = client.post("/admins/cadastrar", json=admin_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Já existe um administrador com esse email"


def test_cpf_ja_cadastrado_como_admin():
    admin_data = {
        "nome": "Admin Teste",
        "email": "davidk1k3k@gmail.com",
        "cpf": "12345678900",
        "data_nascimento": "1990-01-01",
        "telefone": "11999999999",
        "cep": "12345678",
        "complemento": "Apto 101",
        "password": "senha123",
        "confirm_password": "senha123",
    }
    client.post("/admins/cadastrar", json=admin_data)
    admin_data["email"] = "unique_admin@test.com"
    response = client.post("/admins/cadastrar", json=admin_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "CPF já cadastrado por outro admin!"


def test_cpf_ja_cadastrado_como_cliente():
    with Session(engine) as session:
        cliente_data = Cliente(
            nome="Cliente Teste",
            email="davidffsousaff@gmail.com",
            cod_confirmacao_email="123456",
            cpf="12345678900",
            data_nascimento="1995-01-01",
            telefone="11988888888",
            cep="12345678",
            complemento="Casa",
            password="senha123",
            pontos_fidelidade=0,
            clube_fidelidade=False,
            cod_indicacao=0,
            status=True
        )
        session.add(cliente_data)
        session.commit()

    admin_data = {
        "nome": "Admin Teste",
        "email": "unique_admin@test.com",
        "cpf": "12345678900",
        "data_nascimento": "1990-01-01",
        "telefone": "11999999999",
        "cep": "12345678",
        "complemento": "Apto 101",
        "password": "senha123",
        "confirm_password": "senha123",
    }
    response = client.post("/admins/cadastrar", json=admin_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "CPF já cadastrado por outro admin!"


def test_senhas_nao_coincidem():
    admin_data = {
        "nome": "Admin Teste",
        "email": "unique_admin@test.com",
        "cpf": "98765432100",
        "data_nascimento": "1990-01-01",
        "telefone": "11999999999",
        "cep": "12345678",
        "complemento": "Apto 101",
        "password": "senha123",
        "confirm_password": "senha_diferente",
    }
    response = client.post("/admins/cadastrar", json=admin_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Senhas não coincidem!"
