from fastapi import FastAPI
from service.connection_manager import manager

from app.routers import auth

app = FastAPI(title="Мессенджер API", description="API для мессенджера", version="1.0")
manager = ConnectionManager()

app.include_router(auth.router)


@app.get("/health")
async def health_check():
    return {"status": "все ок👌"}


@app.get("/")
async def read_root():
    return {"message": "Добро пожаловать в Мессенджер!👋"}