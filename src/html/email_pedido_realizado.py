def template_pedido_realizado(nome, numero_pedido, url, total_pedido, detalhes_itens):
    # Gerar os detalhes dos itens
    itens_html = ""
    for item in detalhes_itens:
        itens_html += f'''
        <tr>
            <td>{item.nome}</td>
            <td>{item.quantidade_estoque}</td>
            <td>R$ {item.preco:.2f}</td>
            <td>R$ {item.preco * item.quantidade_estoque:.2f}</td>
        </tr>
        '''

    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Confirmação de Pedido - Buy Tech</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
            color: #333333;
        }}
        .email-container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border: 1px solid #dddddd;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .email-header {{
            background-color: #4CAF50;
            color: #ffffff;
            padding: 20px;
            text-align: center;
        }}
        .email-body {{
            padding: 20px;
        }}
        .email-footer {{
            background-color: #f4f4f4;
            padding: 10px;
            text-align: center;
            font-size: 12px;
            color: #777777;
        }}
        .btn {{
            display: inline-block;
            background-color: #4CAF50;
            color: #ffffff;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 5px;
            margin-top: 20px;
            font-size: 16px;
        }}
        .btn:hover {{
            background-color: #45a049;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        table th, table td {{
            padding: 10px;
            text-align: left;
            border: 1px solid #dddddd;
        }}
        table th {{
            background-color: #f4f4f4;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <span>Buy Tech</span>
        </div>
        <div class="email-body">
            <h1>Pedido Realizado com Sucesso!</h1>
            <p>Olá, {nome},</p>
            <p>Obrigado por fazer um pedido conosco! Seguem os detalhes do seu pedido:</p>
            <p><strong>Número do Pedido:</strong> {numero_pedido}</p>
            <p><strong>Total:</strong> R$ {total_pedido:.2f}</p>
            
            <h2>Itens do Pedido</h2>
            <table>
                <thead>
                    <tr>
                        <th>Produto</th>
                        <th>Quantidade</th>
                        <th>Preço Unitário</th>
                        <th>Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    {itens_html}
                </tbody>
            </table>

            <p>Estamos processando o seu pedido e em breve ele será enviado.</p>
            <p>Para realizar o pagamento, por favor, clique no botão abaixo:</p>
            <a href="{url}" class="btn">Efetuar Pagamento</a>
        </div>
        <div class="email-footer">
            <p>&copy; 2024 Buy Tech. Todos os direitos reservados.</p>
        </div>
    </div>
</body>
</html>
'''
