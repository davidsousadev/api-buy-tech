from typing import Annotated
from src.auth_utils import get_logged_cliente, get_logged_admin, hash_password, verifica_pagamento, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
from fastapi import APIRouter, Depends, HTTPException, status, Query
from decouple import config
SECRET_KEY = config('SECRET_KEY')

KEY_STORE = config('KEY_STORE')
router = APIRouter()

@router.get("/{token}")
async def confirmar_pagamento(token: str):
    
      # Valida o token
      codigo_de_confirmacao = await verifica_pagamento(token)
      data = codigo_de_confirmacao.split('-')
      numero_do_pedido = {
            "loja": data[0],
            "idcliente": int(data[1]),
            "valor": float(data[2]),
            "opcao_de_pagamento": bool(data[3]),
            "codigo_de_confirmacao": (data[4])
      }
      
      return numero_do_pedido