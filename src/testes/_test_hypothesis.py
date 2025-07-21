from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


from hypothesis import given, strategies as st

@given(
    nome=st.text(min_size=3, max_size=30),
    email=st.emails(),
    cpf=st.from_regex(r"\d{11}"),
    telefone=st.from_regex(r"\(\d{2}\) \d{4,5}-\d{4}"),
    password=st.text(min_size=6, max_size=20)
)
def test_cliente_cadastro_com_hypothesis(nome, email, cpf, telefone, password):
    payload = {
        "nome": nome,
        "email": email,
        "cpf": cpf,
        "telefone": telefone,
        "password": password
    }
    response = client.post("/clientes/cadastrar", json=payload)
    assert response.status_code in (200, 201, 422)  # 422 = validação do FastAPI
