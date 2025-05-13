import os
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.websockets import WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.tables import User

load_dotenv()

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("jwt_utils")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRATION_TIME = int(os.getenv("JWT_EXPIRATION_TIME", 30))


def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=JWT_EXPIRATION_TIME)
    )
    logger.info(f"Создание JWT токена с данными: {data}, срок истечения: {expire}")
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_jwt_token(token: str) -> Optional[dict]:
    logger.debug(f"Верификация JWT токена: {token}")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Ошибка верификации JWT токена: {e}")
        return None


async def get_current_user_ws(token: str, session: AsyncSession):
    try:
        logger.debug(f"Пытаемся декодировать токен (WS): {token}")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        logger.debug(f"WS payload: {payload}")

        user_id = payload.get("user_id")
        if user_id is None:
            email = payload.get("sub")
            if email:
                stmt = select(User).where(User.email == email)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                if user:
                    return user
            raise HTTPException(status_code=401, detail="Неверный токен")
    except jwt.JWTError as e:
        logger.error(f"Ошибка декодирования JWT токена в WS: {e}")
        raise WebSocketDisconnect(code=1008)

    user = await session.get(User, user_id)
    if not user:
        raise WebSocketDisconnect(code=1008)
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
):
    payload = verify_jwt_token(token)
    if payload is None:
        logger.warning("verify_jwt_token вернул None для токена")
        logger.warning("Неверные аутентификационные данные")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    user_id = payload.get("user_id")
    if user_id is None:
        logger.warning(f"Неверный payload токена: {payload}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user = await session.get(User, user_id)
    if not user:
        logger.warning(f"Пользователь не найден: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
