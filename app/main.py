from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, chat

app = FastAPI(title="Мессенджер API", description="API для мессенджера", version="1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(chat.router)

# Статические файлы
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")


@app.get("/health")
async def health_check():
    return {"status": "все ок👌"}
