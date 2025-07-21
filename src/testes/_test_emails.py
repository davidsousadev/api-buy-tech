from unittest.mock import patch
from src.models.emails_models import Email
"""
@patch("src.servicos.email.enviar_email")  # ou o caminho real do módulo
def test_pedido_personalizado_email(mock_enviar, client):
    mock_enviar.return_value = True

    payload = {
        "nome": "Cliente",
        "email": "teste@cliente.com",
        "cpf": "12345678901",
        "telefone": "(11) 99999-9999",
        "password": "123456",
        "confirm_password": "123456",
        "cod_confirmacao_email": "Confirmado",
        "data_nascimento": "1990-01-01",
        "cep": "12345-678",
        "complemento": "Apto 1"
    }
    response = client.post("/clientes/cadastrar", json=payload)
    cliente_id = response.json().get("id")
    assert cliente_id is not None

    equipamento = {
        "gabinete": "simples",
        "placaMae": "asus",
        "processador": "intel_i3",
        "ram": "4gb",
        "ssd": "128gb",
        "fonte": "400w",
        "observacoes": "Teste"
    }
    response = client.post(f"/emails/monteSeuEquipamento/{cliente_id}", json=equipamento)
    assert response.status_code == 200
    mock_enviar.assert_called_once()
"""