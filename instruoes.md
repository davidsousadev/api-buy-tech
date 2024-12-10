# Instalação básica

## Instalação do venv

```sh
    python3 -m venv venv
    source venv/bin/activate
```
## Atualizando pip

```sh
    pip3 install --upgrade pip
```

## Instalação das dependençias

```sh
    pip3 install -r requirements.txt
```

## ADD .env

```
    EMAIL=
    KEY_EMAIL=
    KEY_POST_EMAIL=
    SECRET_KEY= 
    ALGORITHM= 
```

## Roda o projeto

```sh
    fastapi dev src/main.py
```