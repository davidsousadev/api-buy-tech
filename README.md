# API do projeto - > [BUY TECH](https://github.com/davidsousadev/buy-tech)

# Próximos passos

- > Aplicar Cupons as vendas e verificar
- > Confirmar pagamento
- > Pontos Fidelidade
- > Clube fidelidade
- > Realizar todos os processos de fluxo via e-mail

# Estrutura inicial

```plaintext
api-buy-tech/
├── src/
│   │
│   ├── controllers/                   # Logica das Rotas
│   │   ├── admins_controller.py       # Rotas dos Admin
│   │   ├── carrinho_controller.py     # Rotas dos Carrinho de Compras
│   │   ├── categorias_controller.py   # Rotas das Categorias
│   │   ├── cupons_controller.py       # Rotas dos Cupons
│   │   ├── emails_controller.py       # Rotas dos E-mails
│   │   ├── products_controller.py     # Rotas dos Produtos
│   │   ├── users_controller.py        # Rotas dos Usuarios
│   │   └── vendas_controller.py       # Rotas das Vendas
│   │
│   ├── models/                        # Modelos de dados
│   │   ├── admins_models.py           # Dados dos Admin
│   │   ├── carrinho_models.py         # Dados dos Carrinhos de Compras
│   │   ├── categorias_models.py       # Dados das Categorias
│   │   ├── cupons_models.py           # Dados dos Cupons
│   │   ├── emails_models.py           # Dados dos E-mails
│   │   ├── products_models.py         # Dados dos Produtos
│   │   ├── users_models.py            # Dados dos Usuarios
│   │   └── vendas_models.py           # Dados das Vendas
│   │
│   │
│   │
│   ├── auth_utils.py     # Arquivo de autenticação de usuários / admins
│   ├── database.py       # Arquivo de configuração de banco de dados 
│   └── main.py           # Arquivo principal de inicialização
│
├── .env                  # Variaveis de ambiente¹
├── .envexample           # Exemplo das Variaveis de ambiente
└── README.md             # Project documentation
```

* ¹Crie um arquivo .env e insira as variaveis conforme o arquivo .envexample