# API do projeto - > [BUY TECH](https://github.com/davidsousadev/buy-tech)

# Próximos passos

- > Implementar os testes urgentemente
- > Refatorar a documentação das rotas, install, requeriments e o proprio README.md
- > Refatorar o cupom de desconto para quantidade disponivel, ultilizada, e registro de que usou
- > Confirmar pagamento, e realizar a atualização tanto nos itens do carrinho, como nos pedidos, vendas ...
- > Realizar o fluxo de cotitas com pagamentos, debitos, creditos, pendencias ...
- > Pontos Fidelidade pela referencia / Pela compra
- > Clube fidelidade (Decidir como vai funcionar a pontuação de desconto para quem fizer parte)
- > Alerta de promoções, verificar antes de realizar o pedido, atualizar o valor dos itens no carrinho
- > Realizar todos os processos de fluxos das operações necessárias via e-mail
- > Implementar a logica de cadastro de revendedores e o cadastro de pessoas juridicas
- > Gerar todas as rotas de relatórios disponibilizando tanto para os clientes quanto para os administradores/revendedores
- > Adicionar relação de comentarios, classificação dos produtos

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