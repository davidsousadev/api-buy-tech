from fastapi import FastAPI
from .email_controller import router as email_router
from fastapi.middleware.cors import CORSMiddleware
from .users_controller import router as user_router
from .database import init_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(email_router, 
                   prefix='/email', 
                   tags=["E-mail"])

app.include_router(router=user_router,
                   tags=["Users"])

init_db()