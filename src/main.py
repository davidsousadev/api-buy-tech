from fastapi import FastAPI
from .email_controller import router as email_router

app = FastAPI()

app.include_router(email_router, 
                   prefix='/email', tags=["E-mail"])