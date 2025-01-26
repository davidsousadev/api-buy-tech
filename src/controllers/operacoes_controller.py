from typing import Annotated
from src.auth_utils import get_logged_cliente, get_logged_admin, hash_password, verifica_pagamento, SECRET_KEY, ALGORITHM, ACCESS_EXPIRES, REFRESH_EXPIRES
from fastapi import APIRouter, Depends, HTTPException, status, Query
from decouple import config
from src.models.clientes_models import SignInClienteRequest, SignUpClienteRequest, Cliente, UpdateClienteRequest, ClienteResponse
from src.models.operacoes_models import Operacao, BaseOperacao
from src.models.pedidos_models import Pedido
from src.models.carrinhos_models import Carrinho
from src.database import get_engine
from sqlmodel import Session, select
from passlib.context import CryptContext
import jwt

SECRET_KEY = config('SECRET_KEY')

KEY_STORE = config('KEY_STORE')
router = APIRouter()

"""

Saldo

Extrato

Debitos

Creditos

Pagamentos

Pendências

"""

# Lista os verbos disponiveis para esse controller
@router.options("", status_code=status.HTTP_200_OK)
async def options_emails():
    return { "methods": ["GET"] }

# Operação de retornar o saldo dos clientes
@router.get("/saldo")
def saldo_dos_clientes(cliente: Annotated[Cliente, Depends(get_logged_cliente)]):
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        statement = select(Cliente).where(Cliente.id==cliente.id)
        cliente_cadastrado = session.exec(statement).first()
        
        if not cliente_cadastrado:
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cliente invalido!"
        )
        
        if cliente_cadastrado.pontos_fidelidade:
            return {
                "saldo": cliente_cadastrado.pontos_fidelidade
                    }

# Operação de retornar o extrato dos clientes
@router.get("/extrato")
def extrato_dos_clientes(cliente: Annotated[Cliente, Depends(get_logged_cliente)]):
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        statement = select(Operacao).where(Operacao.cliente==cliente.id)
        operacoes = session.exec(statement).all()
        
        if operacoes:
            registros = []
            for operacao in operacoes:
                registros.append(operacao)
            return registros
        if not operacoes:
            return []

# Operação de retornar os creditos dos cliente       
@router.get("/creditos")
def creditos_dos_cliente(cliente: Annotated[Cliente, Depends(get_logged_cliente)]):
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(Operacao).where(Operacao.cliente==cliente.id)
        operacoes = session.exec(statement).all()
        
        if not operacoes:
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cliente invalido!"
        )
        # Creditos (Motivo: 1 Referência - 2 Cashback, Tipo: 1 Credito)    
        creditos=[]
        for operacao in operacoes:
            if (operacao.motivo==1 and operacao.tipo==1) or (operacao.motivo==2 and operacao.tipo==1):
                creditos.append(operacao)    
        return creditos

# Operação de retornar os debitos dos clientes    
@router.get("/debitos")
def debitos_dos_clientes(cliente: Annotated[Cliente, Depends(get_logged_cliente)]):
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(Operacao).where(Operacao.cliente==cliente.id)
        operacoes = session.exec(statement).all()
        
        if not operacoes:
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cliente invalido!"
        )
        # Debitos (Motivo: 3 Pagamento, Tipo: 2 Debito)
        debitos=[]
        for operacao in operacoes:
            if operacao.motivo==3 and operacao.tipo==2:
                debitos.append(operacao)   
        return debitos

# Operação de confirmar os pagamentos e fazer as determinadas operacoes
@router.get("/pagamentos/{token}")
async def confirmar_pagamentos(token: str, cliente: Annotated[Cliente, Depends(get_logged_cliente)]):
    
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
    
    # Valida o token
    codigo_de_confirmacao = await verifica_pagamento(token)
    data = codigo_de_confirmacao.split('-')
    if data:
        codigo_de_confirmacao_token = {
              "loja": data[0],
              "idcliente": int(data[1]),
              "valor": float(data[2]),
              "opcao_de_pagamento": bool(data[3]),
              "codigo_de_confirmacao": (data[4]),
              "cupom_de_desconto_data": (data[5]),
              "pontos_resgatados": (data[6])
        }
        if codigo_de_confirmacao_token["idcliente"]!=cliente.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Não e possivel pagar a conta de outro cliente!"
            )
        with Session(get_engine()) as session:
            
            sttm = select(Cliente).where(Cliente.id == cliente.id)
            cliente_to_update = session.exec(sttm).first()

            if not cliente_to_update:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado."
                )

            if cliente_to_update.cod_confirmacao_email != "Confirmado":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="E-mail não confirmado!"
                )
                
            statement = select(Pedido).where(Pedido.cliente == cliente.id,
                                             Pedido.status == True,
                                             Pedido.codigo !=""
                                             )
            pedido = session.exec(statement).first()
            if pedido and len(pedido.codigo) > 6 and pedido.codigo !="" and pedido.status==True:
                # Encontrou, então verifica o codigo de confirmação
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

                is_correct = pwd_context.verify(codigo_de_confirmacao_token["codigo_de_confirmacao"], pedido.codigo)

                if not is_correct:
                  raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail='Codigo de confirmação invalido!')

                pedido.codigo=codigo_de_confirmacao_token["codigo_de_confirmacao"]

                produtos_ids = eval(pedido.produtos)  

                if isinstance(produtos_ids, list):
                    produtos_query = select(Carrinho).where(Carrinho.cliente_id==cliente.id)
                    produtos = session.exec(produtos_query).all()

                    for produto in produtos:
                        produto.codigo = codigo_de_confirmacao_token["codigo_de_confirmacao"]
                        session.add(produto)

                # Salvar as alterações no banco de dados
                session.add(pedido)
                session.commit()
                session.refresh(pedido)
            
            # Realiza as apoerações    
            # Creditos (Motivo: 1 Referência - 2 Cashback, Tipo: 1 Credito)
            # Debitos (Motivo: 3 Pagamento, Tipo: 2 Debito)
            
            # Operação Referência
            if cliente_to_update.cod_indicacao != 0:
                sttm = select(Cliente).where(Cliente.id == cliente_to_update.cod_indicacao)
                cliente_de_indicacao = session.exec(sttm).first()
                if cliente_de_indicacao:
                    cliente_de_indicacao.pontos_fidelidade += 1
                    
                    # Salvar a indicacao
                    session.add(cliente_de_indicacao)
                    session.commit()
                    session.refresh(cliente_de_indicacao)
                    
                    # Cria o operacao de indicacao
                    operacao_indicacao = Operacao(
                    cliente=cliente_de_indicacao.id,
                    valor=1,
                    motivo=1,
                    tipo=1,
                    codigo=codigo_de_confirmacao_token["codigo_de_confirmacao"]
                    )
                    # Salvar a indicacao
                    session.add(operacao_indicacao)
                    session.commit()
                    session.refresh(operacao_indicacao)
            
            # Operação pagamento
            statement = select(Operacao).where(Operacao.codigo==codigo_de_confirmacao_token["codigo_de_confirmacao"], Operacao.motivo==3,
                                Operacao.tipo==2)
            operacao = session.exec(statement).first()

            if operacao:
                raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Pagamento já foi realizado anteriormente!"
            )
            if not operacao:
                # Retira do saldo
                cliente_to_update.pontos_fidelidade -= codigo_de_confirmacao_token["valor"]
                
                # Cria o operacao pagamento
                operacao_pagamento = Operacao(
                    cliente=codigo_de_confirmacao_token["idcliente"],
                    valor=codigo_de_confirmacao_token["valor"],
                    motivo=3,
                    tipo=2,
                    codigo=cliente.id
                )
                
                # Salvar as alterações no banco de dados
                session.add(operacao_pagamento)
                session.commit()
                session.refresh(operacao_pagamento)
            
            # Operação caskback
            cashback = int(codigo_de_confirmacao_token["valor"]/100)
            if cashback>=1:
                cliente_to_update.pontos_fidelidade += cashback  
            else:
                cliente_to_update.pontos_fidelidade += 1
                cashback=1
            
            # Cria o operacao de caskback
            statement = select(Operacao).where(Operacao.codigo==codigo_de_confirmacao_token["codigo_de_confirmacao"], Operacao.motivo==2,Operacao.tipo==1)
            operacao = session.exec(statement).first()

            if operacao:
                raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Caskback não pode ser aplicado pois ja foi aplicado anteriormente!"
            )
            operacao_caskback = Operacao(
            cliente=cliente_to_update.id,
            valor=cashback,
            motivo=2,
            tipo=1,
            codigo=codigo_de_confirmacao_token["codigo_de_confirmacao"]
            )
            # Salvar a indicacao
            session.add(operacao_caskback)
            session.commit()
            session.refresh(operacao_caskback)

            return {
                    "mensage": "Pagamento realizado com sucesso!"
                    }

# Operação de retornar as pendênçias           
@router.get("/pendencias")
async def pendencias_dos_clientes(cliente: Annotated[Cliente, Depends(get_logged_cliente)]):
    
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado!"
        )
    with Session(get_engine()) as session:
        # Verifica pedidos não pagos do cliente
        pedidos = select(Pedido).where(Pedido.cliente == cliente.id)
        pedidos_do_cliente = session.exec(pedidos).all()
        pendencias = []
        for pedido in pedidos_do_cliente:
            if pedido.status==True and len(pedido.codigo) !=6:
                pendencias.append(pedido)
        return pendencias