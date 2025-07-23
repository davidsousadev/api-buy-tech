from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from decouple import config
from sqlmodel import Session, select
from passlib.context import CryptContext

from sqlmodel import Session, select, func

from src.auth_utils import get_logged_cliente,  verifica_pagamento, get_logged_admin
from src.database import get_engine
from src.models.clientes_models import Cliente
from src.models.operacoes_models import Operacao
from src.models.pedidos_models import Pedido
from src.models.carrinhos_models import Carrinho
from src.models.produtos_models import Produto
from src.models.admins_models import Admin
from src.models.cupons_models import Cupom



EMAIL = config('EMAIL')
KEY_EMAIL = config('KEY_EMAIL')
URL = config('URL')
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
            status_code=status.HTTP_200_OK,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        statement = select(Cliente).where(Cliente.id==cliente.id)
        cliente_cadastrado = session.exec(statement).first()
        
        if cliente_cadastrado.pontos_fidelidade:
            return {
                "saldo": cliente_cadastrado.pontos_fidelidade
                    }
        
        if not cliente_cadastrado:
            raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Cliente invalido!"
        )

# Operação de retornar o extrato dos clientes
@router.get("/extrato")
def extrato_dos_clientes(cliente: Annotated[Cliente, Depends(get_logged_cliente)]):
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
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
            status_code=status.HTTP_200_OK,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(Operacao).where(Operacao.cliente==cliente.id)
        operacoes = session.exec(statement).all()
        
        if operacoes:
            
            # Creditos (Motivo: 1 Referência - 2 Cashback, Tipo: 1 Credito)    
            creditos=[]
            for operacao in operacoes:
                if (operacao.motivo==1 and operacao.tipo==1) or (operacao.motivo==2 and operacao.tipo==1):
                    creditos.append(operacao)    
            return creditos
        else:
            return []

# Operação de retornar os debitos dos clientes    
@router.get("/debitos")
def debitos_dos_clientes(cliente: Annotated[Cliente, Depends(get_logged_cliente)]):

    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(Operacao).where(Operacao.cliente==cliente.id)
        operacoes = session.exec(statement).all()
        
        if operacoes:
            
            # Debitos (Motivo: 3 Pagamento, Tipo: 2 Debito)
            debitos=[]
            for operacao in operacoes:
                if operacao.motivo==3 and operacao.tipo==2:
                    debitos.append(operacao)   
            return debitos
    
        if not operacoes:
            return []

# Operação de confirmar os pagamentos e fazer as determinadas operacoes
@router.get("/pagamentos/{token}")
async def confirmar_pagamentos(token: str, cliente: Annotated[Cliente, Depends(get_logged_cliente)]):
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Acesso negado!"
        )
    
    codigo_de_confirmacao = await verifica_pagamento(token)
    data = codigo_de_confirmacao.split('-')

    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido.")

    codigo_de_confirmacao_token = {
        "loja": data[0],
        "idcliente": int(data[1]),
        "valor": float(data[2]),
        "opcao_de_pagamento": bool(data[3]),
        "codigo_de_confirmacao": data[4],
        "cupom_de_desconto_data": data[5],
        "pontos_resgatados": data[6]
    }

    if codigo_de_confirmacao_token["idcliente"] != cliente.id:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Não é possível pagar a conta de outro cliente!"
        )

    with Session(get_engine()) as session:
        try:
            sttm = select(Cliente).where(Cliente.id == cliente.id)
            cliente_to_update = session.exec(sttm).first()

            if not cliente_to_update:
                raise HTTPException(status_code=status.HTTP_200_OK, detail="Usuário não encontrado.")

            if cliente_to_update.cod_confirmacao_email != "Confirmado":
                raise HTTPException(status_code=status.HTTP_200_OK, detail="E-mail não confirmado!")

            # Realiza as operações    
            # Creditos (Motivo: 1 Referência - 2 Cashback, Tipo: 1 Credito)
            # Debitos (Motivo: 3 Pagamento, Tipo: 2 Debito)
            # Retira do saldo
            if codigo_de_confirmacao_token["valor"] <= cliente_to_update.pontos_fidelidade:
                cliente_to_update.pontos_fidelidade -= codigo_de_confirmacao_token["valor"]
            else:
                raise HTTPException(status_code=status.HTTP_200_OK, detail="Pontos fidelidade insuficientes!")

            # Buscar pedido válido
            statement = select(Pedido).where(
                Pedido.cliente == cliente.id,
                Pedido.status == True,
                func.length(Pedido.codigo) > 6
            )
            pedido = session.exec(statement).first()
            if not pedido:
                raise HTTPException(status_code=status.HTTP_200_OK, detail='Pedido inválido!')

            # Verifica código de confirmação
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            if not pwd_context.verify(codigo_de_confirmacao_token["codigo_de_confirmacao"], pedido.codigo):
                raise HTTPException(status_code=status.HTTP_200_OK, detail='Código de confirmação inválido!')

            pedido.codigo = codigo_de_confirmacao_token["codigo_de_confirmacao"]

            # Atualiza carrinhos e estoque
            carrinhos_ids = eval(pedido.carrinhos)
            if isinstance(carrinhos_ids, list):
                carrinhos_query = select(Carrinho).where(
                    Carrinho.cliente_id == cliente.id,
                    Carrinho.status == True,
                    Carrinho.id.in_(carrinhos_ids)
                )
                carrinhos = session.exec(carrinhos_query).all()

                for carrinho in carrinhos:
                    if carrinho.quantidade < 1:
                        raise HTTPException(status_code=status.HTTP_200_OK, detail='Produto no pedido sem estoque!')

                    produto_query = select(Produto).where(Produto.id == carrinho.produto_codigo)
                    produto = session.exec(produto_query).first()

                    if not produto or produto.quantidade_estoque < carrinho.quantidade:
                        raise HTTPException(status_code=status.HTTP_200_OK, detail='Produto no pedido sem estoque!')

                    carrinho.codigo = codigo_de_confirmacao_token["codigo_de_confirmacao"]
                    produto.quantidade_estoque -= carrinho.quantidade

                    session.add(produto)
                    session.add(carrinho)

            session.add(pedido)

            # Atualiza cupom
            statement = select(Cupom).where(Cupom.nome == codigo_de_confirmacao_token["cupom_de_desconto_data"])
            cupom = session.exec(statement).first()
            if cupom:
                cupom.resgatado = True
                cupom.quantidade_de_ultilizacao -= 1
                session.add(cupom)
            
            # Realiza as operações    
            # Creditos (Motivo: 1 Referência - 2 Cashback, Tipo: 1 Credito)
            # Debitos (Motivo: 3 Pagamento, Tipo: 2 Debito)
            # # Operação de indicação
            codigo = cliente_to_update.cod_indicacao
            if not codigo.endswith("x"):
                sttm = select(Cliente).where(Cliente.id == int(codigo))
                cliente_de_indicacao = session.exec(sttm).first()

                if cliente_de_indicacao:
                    cliente_de_indicacao.pontos_fidelidade += 10
                    cliente_to_update.pontos_fidelidade += 10
                    cliente_to_update.cod_indicacao = f"{codigo}x"
                    cliente_to_update.clube_fidelidade = True

                    session.add(cliente_de_indicacao)
                    session.add(cliente_to_update)

                    operacao_indicacao = Operacao(
                        cliente=cliente_de_indicacao.id,
                        valor=1,
                        motivo=1,
                        tipo=1,
                        codigo=codigo_de_confirmacao_token["codigo_de_confirmacao"]
                    )
                    session.add(operacao_indicacao)

            # Verifica se pagamento já foi feito
            statement = select(Operacao).where(
                Operacao.codigo == codigo_de_confirmacao_token["codigo_de_confirmacao"],
                Operacao.motivo == 3,
                Operacao.tipo == 2
            )
            operacao = session.exec(statement).first()
            if operacao:
                raise HTTPException(status_code=status.HTTP_200_OK, detail="Pagamento já foi realizado anteriormente!")

            operacao_pagamento = Operacao(
                cliente=codigo_de_confirmacao_token["idcliente"],
                valor=codigo_de_confirmacao_token["valor"],
                motivo=3,
                tipo=2,
                codigo=cliente.id
            )
            session.add(operacao_pagamento)

            # Clube Fidelidade (grande compra)
            if codigo_de_confirmacao_token["valor"] >= 5000:
                if not cliente_to_update.clube_fidelidade:
                    cliente_to_update.clube_fidelidade = True
                    session.add(cliente_to_update)

            # Realiza as operações    
            # Creditos (Motivo: 1 Referência - 2 Cashback, Tipo: 1 Credito)
            # Debitos (Motivo: 3 Pagamento, Tipo: 2 Debito)
            # Cashback
            cashback = max(1, int(codigo_de_confirmacao_token["valor"] / 100))
            cliente_to_update.pontos_fidelidade += cashback

            statement = select(Operacao).where(
                Operacao.codigo == codigo_de_confirmacao_token["codigo_de_confirmacao"],
                Operacao.motivo == 2,
                Operacao.tipo == 1
            )
            operacao = session.exec(statement).first()
            if operacao:
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="Cashback já foi aplicado anteriormente!"
                )

            operacao_cashback = Operacao(
                cliente=cliente_to_update.id,
                valor=cashback,
                motivo=2,
                tipo=1,
                codigo=codigo_de_confirmacao_token["codigo_de_confirmacao"]
            )
            session.add(operacao_cashback)

            # Final commit de todas alterações
            session.commit()
            session.refresh(cliente_to_update)
            session.refresh(cliente_de_indicacao)

            return {"mensage": "Pagamento realizado com sucesso!"}
        
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Operação de retornar as pendênçias           
@router.get("/pendencias")
async def pendencias_dos_clientes(cliente: Annotated[Cliente, Depends(get_logged_cliente)]):
    
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
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
    
# Operaçoes Admin
# Realiza as operações    
# Creditos (Motivo: 1 Referência - 2 Cashback, Tipo: 1 Credito)
# Debitos (Motivo: 3 Pagamento, Tipo: 2 Debito)

# Lista receitas do Sistema
@router.get("/receitas/admin")
def listar_receitas(admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Acesso negado! Apenas administradores podem listar receitas."
        )

    with Session(get_engine()) as session:
        statement = select(Operacao).where(Operacao.motivo==3,
                                           Operacao.tipo==2) # Pagamentos
        pagamentos = session.exec(statement).all()

        if pagamentos:
                  return pagamentos  
        if not pagamentos:
            raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="Nenhum pagamento Realizado"
                )

# Lista debitos do sistema
@router.get("/cashback/admin")
def listar_debitos(admin: Annotated[Admin, Depends(get_logged_admin)]):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Acesso negado! Apenas administradores podem listar receitas."
        )

    with Session(get_engine()) as session:
        statement = select(Operacao).where(Operacao.motivo==2,
                                           Operacao.tipo==1) # Caskback
        cashback = session.exec(statement).all()

        if cashback:
                  return cashback  
        if not cashback:
            raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="Nenhum pagamento Realizado"
                )

# Listar as receitas do sistema e cashback       
@router.get("/vendas/cashback/admin")
def listar_receitas(
    admin: Annotated[Admin, Depends(get_logged_admin)]
    ):
    if not admin.admin:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Acesso negado! Apenas administradores podem listar receitas."
        )

    with Session(get_engine()) as session:
        buscarPagamentos = select(Operacao).where(Operacao.motivo==3, 
                                           Operacao.tipo==2) # Pagamentos
        pagamentos = session.exec(buscarPagamentos).all()

        buscarCashback = select(Operacao).where(Operacao.motivo==2,
                                           Operacao.tipo==1) # Caskback
        caskback = session.exec(buscarCashback).all()
        creditos = 0
        debitos = 0
        if pagamentos:
             for pag in pagamentos:
                creditos += pag.valor
        if caskback:
            for cash in caskback:
                debitos += cash.valor
           

        return {"total_creditos": round(creditos, 2), "total_debitos": round(debitos, 2)}
            