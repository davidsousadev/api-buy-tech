from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .controllers.email_controller import router as email_router
from .controllers.users_controller import router as user_router
from .controllers.admins_controller import router as admins_router
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
    app.include_router(email_router, prefix='/email', tags=["E-mail"])
    app.include_router(user_router, prefix='/usuarios', tags=["Usuarios"])
    app.include_router(admins_router,prefix='/admins', tags=["Admins"])

    # Inicializar o banco de dados (evite problemas fora do contexto)
    @app.on_event("startup")
    async def startup_event():
        init_db()

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    import os
    # Porta dinâmica para serviços como Render
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
