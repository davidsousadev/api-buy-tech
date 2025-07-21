def template_equipamento_personalizado(cliente_to_equipamento, equipamento):
    return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f4;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    padding: 20px;
                    background-color: #fff;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    background-color: #004AAD;
                    color: white;
                    padding: 10px 0;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    padding: 20px;
                    font-size: 16px;
                }}
                .content p {{
                    margin: 10px 0;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                }}
                .label {{
                    font-weight: bold;
                }}
                .value {{
                    color: #555;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Pedido Personalizado de {cliente_to_equipamento.nome}</h2>
                </div>
                <div class="content">
                    <p><span class="label">Gabinete:</span> <span class="value">{equipamento.gabinete}</span></p>
                    <p><span class="label">Placa-mãe:</span> <span class="value">{equipamento.placaMae}</span></p>
                    <p><span class="label">Processador:</span> <span class="value">{equipamento.processador}</span></p>
                    <p><span class="label">Memória RAM:</span> <span class="value">{equipamento.ram}</span></p>
                    <p><span class="label">SSD:</span> <span class="value">{equipamento.ssd}</span></p>
                    <p><span class="label">Fonte:</span> <span class="value">{equipamento.fonte}</span></p>
                    <p><span class="label">Observações:</span> <span class="value">{equipamento.observacoes}</span></p>
                </div>
                <div class="footer">
                    <p>Este é um e-mail automático, por favor não responda.</p>
                </div>
            </div>
        </body>
        </html>
        """