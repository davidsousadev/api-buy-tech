# 🚀 API do Projeto — [BUY TECH](https://github.com/davidsousadev/buy-tech)

## 📝 Descrição

Esta API foi desenvolvida utilizando **FastAPI** (Python). As instruções de instalação estão disponíveis no arquivo [📄 instrucoes.md](/instrucoes.md).

A estrutura da API atualmente possui **13 grupos de controllers**, conforme apresentados na seção [📂 Estrutura Inicial](#-estrutura-inicial):

- 👤 Admins
- 🧑‍💼 Clientes
- 📧 E-mails
- 🏷️ Categorias
- 🎟️ Cupons
- 🛒 Produtos
- 🛍️ Carrinhos
- 📦 Pedidos
- 🔧 Operações
- 🏪 Revendedores
- 🛒 Carrinhos Revendedor
- 📦 Pedidos Revendedor
- 🔧 Operações Revendedor

Atualmente, a API possui **98 endpoints**, utilizando os métodos HTTP:

- `OPTIONS`
- `GET`
- `POST`
- `PATCH`

> 🔥 **Observação:** Não há rotas de exclusão. Essa é uma estratégia baseada em métricas para recuperar cadastros e carrinhos abandonados, além de fomentar as vendas.

A documentação interativa da API pode ser acessada via **Swagger UI** na rota:  
➡️ [http://0.0.0.0:8000/docs](http://0.0.0.0:8000/docs)

> 🔒 Algumas rotas possuem autenticação via **JWT Token**, utilizando tanto **cookies de sessão**, quanto criptografia para proteger dados sensíveis como senhas e links de pagamentos.

📄 As regras de negócio e detalhes das classes estão descritas no documento de especificação do projeto:  
➡️ [Documento do Projeto](https://cutme.vercel.app/13ECfOSTxd)

---

## 📂 Estrutura Inicial

```plaintext
api-buy-tech/
├── src/
│   ├── controllers/                                   # 🧠 Lógica das rotas
│   │   ├── admins_controller.py                       # 👤 Rotas de Admins
│   │   ├── carrinhos_controller.py                    # 🛍️ Rotas de Carrinhos
│   │   ├── carrinhos_revendedor_controller.py         # 🛍️ Rotas de Carrinhos Revendedor
│   │   ├── categorias_controller.py                   # 🏷️ Rotas de Categorias
│   │   ├── clientes_controller.py                     # 👥 Rotas de Clientes
│   │   ├── cupons_controller.py                       # 🎟️ Rotas de Cupons
│   │   ├── emails_controller.py                       # 📧 Rotas de E-mails
│   │   ├── operacoes_controller.py                    # 🔧 Rotas de Operações
│   │   ├── operacoes_revendedor_controller.py         # 🔧 Rotas de Operações Revendedor
│   │   ├── pedidos_controller.py                      # 📦 Rotas de Pedidos
│   │   ├── pedidos_revendedor_controller.py           # 📦 Rotas de Pedidos Revendedor
│   │   ├── produtos_controller.py                     # 🛒 Rotas de Produtos
│   │   └── revendedores_controller.py                 # 🏪 Rotas de Revendedores
│   │
│   ├── html/                                          # 💌 Templates de E-mails (HTML)
│   │   ├── email_confirmacao.py                       # 📩 E-mail de confirmação de conta
│   │   ├── email_pedido_realizado.py                  # 📦 E-mail de pedido realizado
│   │   └── email_redefinir_senha.py                   # 🔐 E-mail de redefinição de senha
│   │
│   ├── models/                                        # 🗂️ Modelos de dados (ORM)
│   │   ├── admins_models.py                           # 👤 Dados de Admins
│   │   ├── carrinhos_models.py                        # 🛍️ Dados de Carrinhos
│   │   ├── carrinhos_revendedor_models.py             # 🛍️ Dados de Carrinhos Revendedor
│   │   ├── categorias_models.py                       # 🏷️ Dados de Categorias
│   │   ├── clientes_models.py                         # 👥 Dados de Clientes
│   │   ├── cupons_models.py                           # 🎟️ Dados de Cupons
│   │   ├── emails_models.py                           # 📧 Dados de E-mails
│   │   ├── operacoes_models.py                        # 🔧 Dados de Operações
│   │   ├── operacoes_revendedor_models.py             # 🔧 Dados de Operações Revendedor
│   │   ├── pedidos_models.py                          # 📦 Dados de Pedidos
│   │   ├── pedidos_revendedor_models.py               # 📦 Dados de Pedidos Revendedor
│   │   ├── produtos_models.py                         # 🛒 Dados de Produtos
│   │   └── revendedores_models.py                     # 🏪 Dados de Revendedores
│   │
│   ├── tests/                                         # 🧪 Testes automatizados
│   │   ├── _test_cadastro_admin.py                    # 🚧 Teste de cadastro de Admin (em desenvolvimento)
│   │   ├── README.md                                  # 🗒️ Documentação dos testes
│   │   └── test__main.py                              # 🧠 Teste principal
│   │
│   ├── auth_utils.py                                  # 🔐 Autenticação de usuários/admins/revendedores
│   ├── database.py                                    # 🗄️ Configuração do banco de dados
│   └── main.py                                        # 🚀 Arquivo principal de inicialização da API
│
├── .env                                               # 🔑 Variáveis de ambiente¹
├── .envexample                                        # 🔑 Exemplo de variáveis de ambiente
├── Dockerfile                                         # 🐳 Configuração Docker
├── instrucoes.md                                      # 📄 Instruções de instalação²
├── README.md                                          # 📝 Documentação do projeto
└── requirements.txt                                   # 📦 Dependências do projeto

```

* ¹ Crie um arquivo .env e insira as variaveis conforme o arquivo .envexample
* ² Siga as instruções no arquivo [instrucoes.md](instrucoes.md)

## Próximos passos

* Aplicar testes de carga e range em todas os end-points
* Implementar paginação na nas listagens e rolagem infinita
  
* Aplicar condições especiais aos revendedores(como descontos para compra em quantidade...)
* Fluxo dos pedidos (Carrinho, pedido, pagamento, envio, recebimento)
* Ajustar revendedores na rotas de clientes e admins, implementar funcionalidades especiais a eles
* Calcular o frete e aplicar clube fidelidade para quem comprou 5 vezes no mes
* Implementar os testes urgentemente
* Refatorar o cupom de desconto para quantidade disponivel, ultilizada, e registro de que usou
* Clube fidelidade (Decidir como vai funcionar a pontuação de desconto para quem fizer parte)
* Alerta de promoções, verificar antes de realizar o pedido, atualizar o valor dos itens no carrinho
* Implementar Caixa de mensagens
* Realizar todos os processos de fluxos das operações necessárias via e-mail
* Implementar a logica de cadastro de revendedores e o cadastro de pessoas juridicas
* Gerar todas as rotas de relatórios disponibilizando tanto para os clientes quanto para os administradores/revendedores
* Adicionar relação de comentarios, classificação dos produtos
* 🚩 Adicionar logica de banners
* 🫵 Adicionar regras para indicações, as regras estão comentadas em buy-tech -> indicacoes.html

## Passos Realizados

* Admins: Funcionalidades - Listar Admins, Cadastrar Admins, Logar Admins, Autenticar Admins, Atualizar Admins, Atualizar Admins Por Id e Atualizar Status Admins Por Id
* Clientes: Funcionalidades - Atualizar Clientes, Verificar Email, Verificar Cpf, Listar Clientes, Listar Clientes Por Id, Cadastrar Clientes, Logar Clientes, Autenticar Clientes, Desativar Clientes, Atualizar Clientes Por Id e Atualizar Status Clientes Admin Por Id
* E-mails: Email Confirmado, Recuperar Email, Recuperar Senha, Suporte Email e Pedido Personalizado
* Categorias, Options Categorias, Listar Categorias, Cadastrar Categorias, Listar Categorias Por Id e Atualizar Categorias Por Id
* Cupons: Cadastrar Cupons, Verificar Cupons, Listar Cupons, Listar Cupons Por Id e Atualizar Cupons Por Id
* Produtos: Listar Produtos, Cadastrar Produto, Buscar Produto e Atualizar Produto Por Id
* Carrinhos: Listar Carrinho, Cadastrar Item Carrinho, Listar Carrinhos Admin e Atualizar Item No Carrinho Por Id
* Pedidos: Listar Pedidos, Cadastrar Pedido, Listar Pedidos Admin, Listar Pedidos Por Id, Cancelar Pedido Por Id e Cancelar Pedido Por Id Admin
* Operações: Saldo Dos Clientes, Extrato Dos Clientes, Créditos Dos Clientes, Débitos Dos Clientes, Confirmar Pagamentos, Pendências Dos Clientes, Listar Receitas, Listar Débitos e Listar Receitas
* Revendedores: Listar Revendedores, Verificar CNPJ, Cadastrar Revendedores, Logar Revendedores, Autenticar Revendedores, Atualizar Revendedor, Desativar Revendedor, Atualizar Revendedor Admin Por Id e Atualizar Status Admin Revendedor Por Id
* Carrinhos Revendedor: Listar Carrinho, Cadastrar Item Carrinho, Listar Carrinhos Admin e Atualizar Item No Carrinho Por Id
* Pedidos Revendedor: Listar Pedidos, Cadastrar Pedido Revendedor, Listar Pedidos Admin, Listar Pedidos Por Id, Cancelar Pedido Por Id e Cancelar Pedido Por Id Admin
* Operações Revendedor: Saldo Dos Revendedores, Extrato Dos Revendedores, Créditos Dos Revendedores, Débitos Dos Revendedores, Confirmar Pagamentos, Pendências Dos Revendedores, Listar Receitas, Listar Débitos e Listar Receitas
* Refatorar a confirmação de email [Urgente]
* Ajustar todos os retornos para no front não aparecer a conexão com a api / remoção de erros HTTP_4*
* Ajustar logica critica dos carrinhos/ pedidos/ diminuição de produtos no pagamento atualmente diminui -1 inves da quantidade real ou melhor nem diminui. Além disso deve ser ajustada a logica para adicionar ao carrinho o codigo de compra, atualmente não está sento realizada a atualização.
* Adição de atualização nos componentes de pedido personalizados

---

🤝 Contribuições e ajuda no desenvolvimento são sempre bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.