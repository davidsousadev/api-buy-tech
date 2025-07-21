def test_login_cliente(client):
    # Primeiro, cadastre um cliente
    payload = {
    "nome": "Cliente Teste",
    "email": "teste@cliente.com",
    "cpf": "12345678901",
    "telefone": "(11) 99999-9999",
    "password": "123456",
    "confirm_password": "123456",
    "cod_confirmacao_email": "Confirmado",
    "data_nascimento": "2000-01-01",
    "cep": "12345-678",
    "complemento": "Apto 101"
    }


    response = client.post("/clientes/cadastrar", json=payload)
    print("Resposta cadastro cliente:", response.json())
    assert response.status_code == 201, f"Falha ao cadastrar: {response.json()}"
    cliente_id = response.json().get("id")
    assert cliente_id is not None, "Resposta não retornou ID"


    # Agora tente logar
    login = {
        "email": payload["email"],
        "password": payload["password"]
    }
    response = client.post("/clientes/logar", json=login)
    assert response.status_code == 200
    assert "access_token" in response.json()
