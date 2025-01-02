# API do projeto - > [BUY TECH](https://github.com/davidsousadev/buy-tech)

# Próximos passos

- > Ajustar envio de e-mail com dados do pedido, codigo de autenticação
- > Confirmar pagamento
- > Pontos Fidelidade
- > Clube fidelidade
- > Alerta de promoções
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
│   │   ├── produtos_controller.py     # Rotas dos Produtos
│   │   ├── clientes_controller.py     # Rotas dos Clientes
│   │   └── pedidos_controller.py      # Rotas das Pedidos
│   │
│   ├── models/                        # Modelos de dados
│   │   ├── admins_models.py           # Dados dos Admin
│   │   ├── carrinho_models.py         # Dados dos Carrinhos de Compras
│   │   ├── categorias_models.py       # Dados das Categorias
│   │   ├── cupons_models.py           # Dados dos Cupons
│   │   ├── emails_models.py           # Dados dos E-mails
│   │   ├── produtos_models.py         # Dados dos Produtos
│   │   ├── clientes_models.py         # Dados dos Clientes
│   │   └── pedidos_models.py          # Dados das Pedidos
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