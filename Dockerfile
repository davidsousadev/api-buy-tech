# 1. Máquina base com Python
FROM python:3.11.6-slim-bullseye

# 2. Definir diretório de trabalho
WORKDIR /home/app

# 3. Copiar dependências primeiro para otimizar o cache
COPY ./requirements.txt .

# 4. Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o restante dos arquivos do projeto
COPY . .

# 6. Expor a porta do container
EXPOSE 8000

# 7. Rodar a aplicação
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
