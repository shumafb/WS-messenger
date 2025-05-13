from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("messenger_api")

from app.routers import auth, chat

app = FastAPI(title="Мессенджер API", description="API для мессенджера", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)

logger.info("Маршруты подключены: auth, chat")

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")


@app.get("/health")
async def health_check():
    logger.info("Health check endpoint был вызван")
    return {"status": "все ок👌"}
