def template_redefinir_senha(nome, password):
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta nome="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recuperar de Senha - Buy Tech</title>
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
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <span>Buy Tech</span>
        </div>
        <div class="email-body">
            <h1>Recuperar de Senha</h1>
            <p>Olá, {nome}</p>
            <p>Recebemos uma solicitação para redefinir sua senha. </p>
            <p><h5>Sua nova senha faça o login e altere:</h5></p>
            <h3>{password}</h3>
        </div>
        <div class="email-footer">
            <p>&copy; 2024 Buy Tech. Todos os direitos reservados.</p>
        </div>
    </div>
</body>
</html>
'''
