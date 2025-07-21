from factory import Factory, Faker
from src.models.clientes_models import Cliente

class ClienteFactory(Factory):
    class Meta:
        model = Cliente

    nome = Faker("name")
    email = Faker("email")
    cpf = Faker("cpf")
    telefone = Faker("phone_number")
    cod_confirmacao_email = "Confirmado"
    password = Faker("password")
