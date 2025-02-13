def template_pedido_realizado(nome, numero_pedido, url, itens_carrinho, frete, opcao_de_pagamento, desconto=0.0, nome_cupom=None, pontos_resgatados=0):
    # Converte valores para float para garantir a precisão
    frete = float(frete)
    desconto = float(desconto)
    pontos_resgatados = float(pontos_resgatados)
    
    total_itens = sum(float(item["preco"]) * float(item["quantidade"]) for item in itens_carrinho)
    total_com_desconto = max((total_itens - desconto - pontos_resgatados + frete), 0.0)
    
    # Traduz a opção de pagamento para o texto correspondente
    if opcao_de_pagamento is True:
        opcao_de_pagamento = "Boleto"
    else:
        opcao_de_pagamento = "À vista"
        
    # Gera os detalhes dos itens em HTML
    itens_html = ""
    for item in itens_carrinho:
        preco = float(item["preco"])
        quantidade = float(item["quantidade"])
        subtotal = preco * quantidade
        itens_html += f'''
        <tr>
            <td>{item["nome"]}</td>
            <td>{int(quantidade)}</td>
            <td>R$ {preco:.2f}</td>
            <td>R$ {subtotal:.2f}</td>
        </tr>
        '''

    # Retorna o template HTML do pedido
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Confirmação de Pedido - Buy Tech</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; }}
        .email-container {{ max-width: 600px; margin: auto; background-color: #fff; border-radius: 8px; padding: 20px; }}
        .email-header {{ background-color: #4CAF50; color: #fff; padding: 20px; text-align: center; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <h1>Buy Tech</h1>
        </div>
        <div class="email-body">
            <h2>Olá, {nome}</h2>
            <p>Seu pedido foi realizado com sucesso! Seguem os detalhes:</p>
            <p><strong>Número do Pedido:</strong> {numero_pedido}</p>
            <p><strong>Opção de pagamento:</strong> {opcao_de_pagamento}</p>
            <p><strong>Total dos Itens:</strong> R$ {total_itens:.2f}</p>
            <p><strong>Frete:</strong> R$ {frete:.2f}</p>
            <p><strong>Pontos Fidelidade Resgatados:</strong> R$ {pontos_resgatados:.2f}</p>
            <p><strong>Desconto:</strong> R$ {desconto:.2f} ({nome_cupom or 'Sem cupom'})</p>
            <p><strong>Total com Desconto:</strong> R$ {total_com_desconto:.2f}</p>
            <h3>Itens do Pedido</h3>
            <table>
                <tr>
                    <th>Produto</th>
                    <th>Quantidade</th>
                    <th>Preço Unitário</th>
                    <th>Subtotal</th>
                </tr>
                {itens_html}
            </table>
        </div>
    </div>
</body>
</html>
'''
