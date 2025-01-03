def template_pedido_realizado(nome, numero_pedido, url, total_itens_carrinho, detalhes_itens, cupom_de_desconto=0, nome_cupom_desconto=None, pontos_fidelidade_resgatados=0):

    # Calcular o total do pedido
    total_itens = sum(item["preco"] * item["quantidade"] for item in detalhes_itens)
    total_com_desconto = total_itens - cupom_de_desconto - pontos_fidelidade_resgatados

    if total_com_desconto == total_itens_carrinho:
        print("ok")

    # Gerar os detalhes dos itens
    itens_html = ""
    for item in detalhes_itens:
        itens_html += f'''
        <tr>
            <td>{item["nome"]}</td>
            <td>{item["quantidade"]}</td>
            <td>R$ {item["preco"]:.2f}</td>
            <td>R$ {item["preco"] * item["quantidade"]:.2f}</td>
        </tr>
        '''

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
            <p><strong>Total dos Itens:</strong> R$ {total_itens:.2f}</p>
            <p><strong>Desconto:</strong> R$ {cupom_de_desconto:.2f} ({nome_cupom_desconto or 'Sem cupom'})</p>
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
            <a href="{url}" style="display: block; background-color: #4CAF50; color: #fff; text-align: center; padding: 10px; border-radius: 5px; text-decoration: none;">Efetuar Pagamento</a>
        </div>
    </div>
</body>
</html>
'''
