from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from mangum import Mangum

# Importação de todos os controladores
from .controllers.emails_controller import router as email_router
from .controllers.clientes_controller import router as clientes_router
from .controllers.admins_controller import router as admins_router
from .controllers.cupons_controller import router as cupons_router
from .controllers.categorias_controller import router as categorias_router
from .controllers.produtos_controller import router as produtos_router
from .controllers.pedidos_controller import router as pedidos_router
from .controllers.carrinhos_controller import router as carrinho_router
from .controllers.operacoes_controller import router as operacoes_router
from .controllers.revendedores_controller import router as revendedores_router
from .controllers.pedidos_revendedor_controller import router as pedidos_revendedor_router
from .controllers.carrinhos_revendedor_controller import router as carrinho_revendedor_router
from .controllers.operacoes_revendedor_controller import router as operacoes_revendedor_router

from .database import init_db


def create_app():
    # Inicializa a aplicação
    app = FastAPI(
        title="API Buy Tech",
        description="API para gerenciar operações do sistema Buy Tech.",
        version="1.0.0",
    )

    # Configuração de CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware TrustedHost
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"], 
    )

    # Registro das rotas
    app.include_router(admins_router, prefix="/admins", tags=["Admins"])
    app.include_router(clientes_router, prefix="/clientes", tags=["Clientes"])
    app.include_router(email_router, prefix="/emails", tags=["E-mails"])
    app.include_router(categorias_router, prefix="/categorias", tags=["Categorias"])
    app.include_router(cupons_router, prefix="/cupons", tags=["Cupons"])
    app.include_router(produtos_router, prefix="/produtos", tags=["Produtos"])
    app.include_router(carrinho_router, prefix="/carrinhos", tags=["Carrinhos"])
    app.include_router(pedidos_router, prefix="/pedidos", tags=["Pedidos"])
    app.include_router(operacoes_router, prefix="/operacoes", tags=["Operações"])
    app.include_router(revendedores_router, prefix="/revendedores", tags=["Revendedores"])
    app.include_router(carrinho_revendedor_router, prefix="/carrinhos_revendedor", tags=["Carrinhos Revendedor"])
    app.include_router(pedidos_revendedor_router, prefix="/pedidos_revendedor", tags=["Pedidos Revendedor"])
    app.include_router(operacoes_revendedor_router, prefix="/operacoes_revendedor", tags=["Operações Revendedor"])

    # Inicialização do banco de dados
    init_db()

    return app


app = create_app()

handler = Mangum(app)

# Execução local
if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
