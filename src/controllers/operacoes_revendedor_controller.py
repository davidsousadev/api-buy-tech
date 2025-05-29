from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from decouple import config
from sqlmodel import Session, select
from passlib.context import CryptContext

from sqlmodel import Session, select, func

from src.auth_utils import get_logged_revendedor,  verifica_pagamento, get_logged_admin
from src.database import get_engine
from src.models.revendedores_models import Revendedor
from src.models.operacoes_revendedor_models import OperacaoRevendedor
from src.models.pedidos_revendedor_models import PedidoRevendedor
from src.models.carrinhos_revendedor_models import CarrinhoRevendedor
from src.models.admins_models import Admin


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

# Operação de retornar o saldo dos revendedors
@router.get("/saldo")
def saldo_dos_revendedors(revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)]):
    if not revendedor:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        statement = select(Revendedor).where(Revendedor.id==revendedor.id)
        revendedor_cadastrado = session.exec(statement).first()
        
        if revendedor_cadastrado.pontos_fidelidade:
            return {
                "saldo": revendedor_cadastrado.pontos_fidelidade
                    }

# Operação de retornar o extrato dos revendedors
@router.get("/extrato")
def extrato_dos_revendedors(revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)]):
    if not revendedor:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Acesso negado!"
        )
        
    with Session(get_engine()) as session:
        statement = select(OperacaoRevendedor).where(OperacaoRevendedor.revendedor_id==revendedor.id)
        operacoes = session.exec(statement).all()
        
        if operacoes:
            registros = []
            for operacao in operacoes:
                registros.append(operacao)
            return registros
        if not operacoes:
            return []

# Operação de retornar os creditos dos revendedor       
@router.get("/creditos")
def creditos_dos_revendedor(revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)]):
    if not revendedor:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(OperacaoRevendedor).where(OperacaoRevendedor.revendedor_id==revendedor.id)
        operacoes = session.exec(statement).all()
       
        # Creditos (Motivo: 1 Referência - 2 Cashback, Tipo: 1 Credito)    
        creditos=[]
        for operacao in operacoes:
            if (operacao.motivo==1 and operacao.tipo==1) or (operacao.motivo==2 and operacao.tipo==1):
                creditos.append(operacao)    
        return creditos

# Operação de retornar os debitos dos revendedors    
@router.get("/debitos")
def debitos_dos_revendedors(revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)]):
    if not revendedor:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Acesso negado!"
        )

    with Session(get_engine()) as session:
        statement = select(OperacaoRevendedor).where(OperacaoRevendedor.revendedor_id==revendedor.id)
        operacoes = session.exec(statement).all()
        
        # Debitos (Motivo: 3 Pagamento, Tipo: 2 Debito)
        debitos=[]
        for operacao in operacoes:
            if operacao.motivo==3 and operacao.tipo==2:
                debitos.append(operacao)   
        return debitos

# Operação de confirmar os pagamentos e fazer as determinadas operacoes
@router.get("/pagamentos/{token}")
async def confirmar_pagamentos(token: str, revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)]):
    
    if not revendedor:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Acesso negado!"
        )
    
    # Valida o token
    codigo_de_confirmacao = await verifica_pagamento(token)
    data = codigo_de_confirmacao.split('-')
    if data:
        codigo_de_confirmacao_token = {
              "loja": data[0],
              "idrevendedor": int(data[1]),
              "valor": float(data[2]),
              "opcao_de_pagamento": bool(data[3]),
              "codigo_de_confirmacao": (data[4]),
              "cupom_de_desconto_data": (data[5]),
              "pontos_resgatados": (data[6])
        }
        if codigo_de_confirmacao_token["idrevendedor"]!=revendedor.id:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Não e possivel pagar a conta de outro revendedor!"
            )
        with Session(get_engine()) as session:
            
            sttm = select(Revendedor).where(Revendedor.id == revendedor.id)
            revendedor_to_update = session.exec(sttm).first()

            if not revendedor_to_update:
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="Usuário não encontrado."
                )

            if revendedor_to_update.cod_confirmacao_email != "Confirmado":
                raise HTTPException(
                    status_code=status.HTTP_200_OK, 
                    detail="E-mail não confirmado!"
                )
            
            

            statement = select(PedidoRevendedor).where(PedidoRevendedor.revendedor_id == revendedor.id,
                                             PedidoRevendedor.status == True,
                                             func.length(PedidoRevendedor.codigo) > 6
                                             )
            
            pedido = session.exec(statement).first()
            if pedido and len(pedido.codigo) > 6 and pedido.codigo !="" and pedido.status==True:
                # Encontrou, então verifica o codigo de confirmação
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

                is_correct = pwd_context.verify(codigo_de_confirmacao_token["codigo_de_confirmacao"], pedido.codigo)
                if not is_correct:
                  raise HTTPException(
                    status_code=status.HTTP_200_OK, 
                    detail='Codigo de confirmação invalido!')

                pedido.codigo=codigo_de_confirmacao_token["codigo_de_confirmacao"]

                produtos_ids = eval(pedido.produtos)  

                if isinstance(produtos_ids, list):
                    produtos_query = select(CarrinhoRevendedor).where(CarrinhoRevendedor.revendedor_id==revendedor.id,
                                                            CarrinhoRevendedor.status == True,
                                                            func.length(CarrinhoRevendedor.codigo) >= 6)
                    produtos = session.exec(produtos_query).all()

                    for produto in produtos:
                        if produto.quantidade > 1:
                            produto.codigo = codigo_de_confirmacao_token["codigo_de_confirmacao"]
                            produto.quantidade -= 1
                        else: 
                            raise HTTPException(
                                status_code=status.HTTP_200_OK, 
                                detail='Produto no pedido sem estoque!')
                        session.add(produto)

                # Salvar as alterações no banco de dados
                session.add(pedido)
                session.commit()
                session.refresh(pedido)
            
            # Realiza as apoerações    
            # Creditos (Motivo: 1 Referência - 2 Cashback, Tipo: 1 Credito)
            # Debitos (Motivo: 3 Pagamento, Tipo: 2 Debito)
            
            # Operação Referência
            if revendedor_to_update.cod_indicacao != 0:
                sttm = select(Revendedor).where(Revendedor.id == revendedor_to_update.cod_indicacao)
                revendedor_de_indicacao = session.exec(sttm).first()
                if revendedor_de_indicacao:
                    revendedor_de_indicacao.pontos_fidelidade += 1
                    revendedor_to_update.pontos_fidelidade += 1
                    
                    # Verifica se o revendedor de indicação já é do clube fidelidade
                    revendedor_to_update.clube_fidelidade = True
                    # Salvar a indicacao
                    session.add(revendedor_de_indicacao)
                    session.commit()
                    session.refresh(revendedor_de_indicacao)
                    
                    # Cria o operacao de indicacao
                    operacao_revendedor_indicacao = OperacaoRevendedor(
                    revendedor_id=revendedor_de_indicacao.id,
                    valor=1,
                    motivo=1,
                    tipo=1,
                    codigo=codigo_de_confirmacao_token["codigo_de_confirmacao"]
                    )
                    # Salvar a indicacao
                    session.add(operacao_revendedor_indicacao)
                    session.commit()
                    session.refresh(operacao_revendedor_indicacao)
            
            # Operação pagamento
            statement = select(OperacaoRevendedor).where(OperacaoRevendedor.codigo==codigo_de_confirmacao_token["codigo_de_confirmacao"],       
                                               OperacaoRevendedor.motivo==3,
                                               OperacaoRevendedor.tipo==2)
            operacao = session.exec(statement).first()

            if operacao:
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="Pagamento já foi realizado anteriormente!"
                    )
            
            if not operacao:
               
                # Cria o operacao pagamento
                operacao_revendedor_pagamento = OperacaoRevendedor(
                    revendedor_id=codigo_de_confirmacao_token["idrevendedor"],
                    valor=codigo_de_confirmacao_token["valor"],
                    motivo=3,
                    tipo=2,
                    codigo=revendedor.id
                )
                
                # Salvar as alterações no banco de dados
                session.add(operacao_revendedor_pagamento)
                session.commit()
                session.refresh(operacao_revendedor_pagamento)
            
            # Operação caskback
            cashback = int(codigo_de_confirmacao_token["valor"]/100)
            if cashback>=1:
                revendedor_to_update.pontos_fidelidade += cashback  
            else:
                revendedor_to_update.pontos_fidelidade += 1
                cashback=1
            print(codigo_de_confirmacao_token["codigo_de_confirmacao"])
            # Cria o operacao de caskback
            statement = select(OperacaoRevendedor).where(OperacaoRevendedor.codigo==codigo_de_confirmacao_token["codigo_de_confirmacao"], 
                                               OperacaoRevendedor.motivo==2,
                                               OperacaoRevendedor.tipo==1)
            operacao = session.exec(statement).first()

            if operacao:
                raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Caskback não pode ser aplicado pois ja foi aplicado anteriormente!"
            )
            operacao_revendedor_caskback = OperacaoRevendedor(
            revendedor_id=revendedor_to_update.id,
            valor=cashback,
            motivo=2,
            tipo=1,
            codigo=codigo_de_confirmacao_token["codigo_de_confirmacao"]
            )
            # Salvar a indicacao
            session.add(operacao_revendedor_caskback)
            session.commit()
            session.refresh(operacao_revendedor_caskback)

            return { "mensage": "Pagamento realizado com sucesso!" }

# Operação de retornar as pendênçias           
@router.get("/pendencias")
async def pendencias_dos_revendedors(revendedor: Annotated[Revendedor, Depends(get_logged_revendedor)]):
    
    if not revendedor:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Acesso negado!"
        )
    with Session(get_engine()) as session:
        # Verifica pedidos não pagos do revendedor
        pedidos = select(PedidoRevendedor).where(PedidoRevendedor.revendedor_id == revendedor.id)
        pedidos_do_revendedor = session.exec(pedidos).all()
        pendencias = []
        for pedido in pedidos_do_revendedor:
            if pedido.status==True and len(pedido.codigo) !=6:
                pendencias.append(pedido)
        return pendencias
    
# Operaçoes Admin
# Realiza as apoerações    
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
        statement = select(OperacaoRevendedor).where(OperacaoRevendedor.motivo==3,
                                           OperacaoRevendedor.tipo==2) # Pagamentos
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
        statement = select(OperacaoRevendedor).where(OperacaoRevendedor.motivo==2,
                                           OperacaoRevendedor.tipo==1) # Caskback
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
        buscarPagamentos = select(OperacaoRevendedor).where(OperacaoRevendedor.motivo==3, 
                                           OperacaoRevendedor.tipo==2) # Pagamentos
        pagamentos = session.exec(buscarPagamentos).all()

        buscarCashback = select(OperacaoRevendedor).where(OperacaoRevendedor.motivo==2,
                                           OperacaoRevendedor.tipo==1) # Caskback
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
            