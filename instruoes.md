# Instalação básica

## Instalação do venv

```sh
    python3 -m venv venv-buy
    source venv-buy/bin/activate
```
## Atualizando pip

```sh
    pip3 install --upgrade pip
```

## Instalação das dependençias

```sh
    pip3 install -r requirements.txt
```

## Coamndo para cria .env *Adicione as variaveis

```
    cp .envexample .env
```

## Gera secure random secret key
```sh
    openssl rand -hex 32 # Variavel SECRET_KEY
```
### Examples:
- > KEY_EMAIL= halv wpqs mgpl epxj
- > ALGORITHM = HS256
- > URL=http://127.0.0.1:8000

## Roda o projeto *Só depois de adicionar as variaveis

```sh
    fastapi dev src/main.py
```