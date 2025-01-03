from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .controllers.emails_controller import router as email_router
from .controllers.clientes_controller import router as clientes_router
from .controllers.admins_controller import router as admins_router
from .controllers.cupons_controller import router as cupons_router
from .controllers.categorias_controller import router as categorias_router
from .controllers.produtos_controller import router as produtos_router
from .controllers.pedidos_controller import router as pedidos_router
from .controllers.carrinhos_controller import router as carrinho_router
from .controllers.pagamentos_controller import router as pagamentos_router


#from .teste.teste_numero_pedido.ok import router as teste_numero_pedido_router

from .database import init_db

def create_app():
    # Inicializa a aplicação FastAPI
    app = FastAPI()

    # Configuração de CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em produção, especifique os domínios permitidos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rotas teste

    #app.include_router(teste_numero_pedido_router, prefix='/testes', tags=["Testes"])

    # Rotas
    app.include_router(pagamentos_router, prefix='/pagamentos', tags=["Pagamentos"])
    app.include_router(categorias_router, prefix='/categorias', tags=["Categorias"])
    app.include_router(produtos_router, prefix='/produtos', tags=["Produtos"])
    app.include_router(carrinho_router, prefix='/carrinhos', tags=["Carrinhos"])
    app.include_router(pedidos_router, prefix='/pedidos', tags=["Pedidos"])
    app.include_router(email_router, prefix='/emails', tags=["E-mails"])
    app.include_router(clientes_router, prefix='/clientes', tags=["Clientes"])
    app.include_router(admins_router, prefix='/admins', tags=["Admins"])
    app.include_router(cupons_router, prefix='/cupons', tags=["Cupons"])
    
    
    # Inicia o banco
    init_db()

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    import os
    # Porta dinâmica para serviços como Render
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
