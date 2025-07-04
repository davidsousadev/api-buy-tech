from datetime import datetime

anoAtual = datetime.now().strftime("%Y")

def template_confirmacao(nome, url):
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta nome="viewport" content="width=device-width, initial-scale=1.0">
    <title>Confirmação de Email - Buy Tech</title>
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
            background-color: #004AAD;
            color: #ffffff;
            padding: 20px;
            text-align: center;
        }}
        .email-body {{
            padding: 20px;
        }}
        .btn {{
            display: inline-block;
            background-color: #15B0F8;
            color: #ffffff;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 5px;
            margin-top: 20px;
            font-size: 16px;
        }}
        .btn:hover {{
            background-color: #3a83a5;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <h1>Buy Tech</h1>
        </div>
        <div class="email-body">
            <h1>Confirmação de Email</h1>
            <p>Olá, {nome}</p>
            <p>Obrigado por escolher a Buy Tech! Por favor, confirme seu email para completar o processo.</p>
            <a href="{url}" class="btn">Confirmar Email</a>
            <p>Se você não solicitou esta ação, ignore este email.</p>
        </div>
        <div class="email-footer">
            <p>&copy; {anoAtual} Buy Tech. Todos os direitos reservados.</p>
        </div>
    </div>
</body>
</html>
'''