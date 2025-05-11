from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.routers import auth, chat

app = FastAPI(title="Мессенджер API", description="API для мессенджера", version="1.0")


app.include_router(auth.router)
app.include_router(chat.router)


@app.get("/health")
async def health_check():
    return {"status": "все ок👌"}


@app.get("/")
async def read_root():
    return FileResponse("app/static/index.html")
