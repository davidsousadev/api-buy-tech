from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .controllers.emails_controller import router as email_router
from .controllers.users_controller import router as user_router
from .controllers.admins_controller import router as admins_router
from .controllers.products_controller import router as products_router
from .controllers.categorias_controller import router as categorias_router
from .controllers.vendas_controller import router as vendas_router
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

    # Rotas
    app.include_router(vendas_router,prefix='/vendas', tags=["Vendas"])
    app.include_router(categorias_router,prefix='/categorias', tags=["Categorias"])
    app.include_router(products_router,prefix='/produtos', tags=["Produtos"])
    app.include_router(email_router, prefix='/email', tags=["E-mail"])
    app.include_router(user_router, prefix='/usuarios', tags=["Usuarios"])
    app.include_router(admins_router,prefix='/admins', tags=["Admins"])
    
    
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
