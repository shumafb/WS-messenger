from fastapi import FastAPI

from app.routers import auth

app = FastAPI(title="Мессенджер API",
            description="API для мессенджера",
            version="1.0")

app.include_router(auth.router)

@app.get("/health")
async def health_check():
    return {"status": "все ок👌"}

@app.get("/")
async def read_root():
    return {"message": "Добро пожаловать в Мессенджер!👋"}