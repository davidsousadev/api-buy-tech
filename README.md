# API do projeto - > [BUY TECH](https://github.com/davidsousadev/buy-tech)

# Estrutura inicial

```plaintext
api-buy-tech/
├── src/
│   │
│   ├── controllers/                   # Logica das Rotas
│   │   ├── admins_controller.py       # Rotas dos Admin
│   │   ├── carrinho_controller.py     # Rotas dos Carrinho de Compras
│   │   ├── categorias_controller.py   # Rotas das Categorias
│   │   ├── clientes_controller.py     # Rotas dos Clientes
│   │   ├── cupons_controller.py       # Rotas dos Cupons
│   │   ├── emails_controller.py       # Rotas dos E-mails
│   │   ├── operacoes_controller.py    # Rotas das Operações
│   │   ├── pedidos_controller.py      # Rotas das Pedidos
│   │   ├── produtos_controller.py     # Rotas dos Produtos
│   │   └── revendedores_controller.py # Rotas dos Revendedores
│   │
│   ├── html/                          # Templates de E-mail HTML
│   │   ├── email_confirmacao.py       # E-mail de confirmação de conta
│   │   ├── email_pedido_realizado.py  # E-mail de pedido solicitado
│   │   └── email_redefinir_senha.py   # E-mail de redefinição de senha
│   │
│   ├── models/                        # Modelos de dados
│   │   ├── admins_models.py           # Dados dos Admin
│   │   ├── carrinho_models.py         # Dados dos Carrinhos de Compras
│   │   ├── categorias_models.py       # Dados das Categorias
│   │   ├── clientes_models.py         # Dados dos Clientes
│   │   ├── cupons_models.py           # Dados dos Cupons
│   │   ├── emails_models.py           # Dados dos E-mails
│   │   ├── operacoes_models.py        # Dados dos Operações
│   │   ├── pedidos_models.py          # Dados das Pedidos
│   │   ├── produtos_models.py         # Dados dos Produtos
│   │   └── revendedores_models.py     # Dados dos Revendedores
│   │
│   ├── auth_utils.py     # Arquivo de autenticação de usuários / admins / revendedores
│   ├── database.py       # Arquivo de configuração de banco de dados 
│   └── main.py           # Arquivo principal de inicialização
│
├── .env                  # Variaveis de ambiente¹
├── .envexample           # Exemplo das Variaveis de ambiente
├── instrucoes.md         # Arquivo com as instruções de instalação
├── README.md             # Project documentation
└── requirements.txt      # Arquivo com as blibiotecas ultilizadas no projeto²
```

* ¹ Crie um arquivo .env e insira as variaveis conforme o arquivo .envexample
* ² Siga as instruções no arquivo [instrucoes.md](instrucoes.md)

# Próximos passos

- > Aplicar condicoes especiais aos revendedores(como descontos para compra em quantidade...)
- > Refatorar verificar cpf / email em clientes_controller
- > *Fluxo dos pedidos (Carrinho, pedido, pagamento, envio, recebimento)
- > Ajustar revendedores na rotas de clientes e admins, implementar funcionalidades especiais a eles
- > Calcular o frete e aplicar clube fidelidade para quem comprou 5 vezes no mes
- > Implementar os testes urgentemente
- > Refatorar a documentação das rotas, install, requeriments e o proprio README.md
- > Refatorar o cupom de desconto para quantidade disponivel, ultilizada, e registro de que usou
- > Clube fidelidade (Decidir como vai funcionar a pontuação de desconto para quem fizer parte)
- > Alerta de promoções, verificar antes de realizar o pedido, atualizar o valor dos itens no carrinho
- > Implementar Caixa de mensagens
- > Realizar todos os processos de fluxos das operações necessárias via e-mail
- > Implementar a logica de cadastro de revendedores e o cadastro de pessoas juridicas
- > Gerar todas as rotas de relatórios disponibilizando tanto para os clientes quanto para os administradores/revendedores
- > Adicionar relação de comentarios, classificação dos produtos

# Passos Realizados

- > ~~Recuperar cadastro via(CPF, e-mail)~~
- > ~~Recuperar senha via(CPF, e-mail)~~
- > ~~Ajustar envio de e-mail com dados do pedido, codigo de autenticação~~
- > ~~Confirmar pagamento, e realizar a atualização tanto nos itens do carrinho, como nos pedidos, vendas ...~~
- > ~~Realizar o fluxo de cotitas com pagamentos, debitos, creditos, pendencias ...~~
- > ~~Pontos Fidelidade pela referencia / Pela compra~~
- > ~~Adição de comentarios em todas as rotas~~
