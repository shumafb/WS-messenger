from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")


@app.get("/health")
async def health_check():
    return {"status": "все ок👌"}
