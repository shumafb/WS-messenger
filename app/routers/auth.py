from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_async_session
from ..models.tables import User as ORMUser
from ..schemas.auth import LoginRequest, TokenResponse
from ..schemas.tables import User, UserCreate
from ..utils.jwt import create_jwt_token, verify_jwt_token

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("auth")

router = APIRouter(
    tags=["auth"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


async def check_login(email, password, db):
    logger.info(f"Попытка входа пользователя: {email}")
    stmt = select(ORMUser).where(ORMUser.email == email)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    logger.warning(f"Пользователь не найден: {email}")
    if not db_user:
        raise HTTPException(status_code=400, detail="Пользователь не найден.")
    if not pwd_context.verify(password, db_user.password):
        logger.warning(f"Неверный пароль для пользователя: {email}")
        raise HTTPException(status_code=400, detail="Неверный пароль.")
    logger.info(f"Успешный вход пользователя: {email}")
    return db_user


async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_session)
) -> ORMUser:
    logger.debug(f"Верификация токена: {token}")
    payload = verify_jwt_token(token)
    if not payload:
        logger.warning("Неверный или истекший токен")
        raise HTTPException(
            status_code=401,
            detail="Неверный или истекший токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(ORMUser).where(ORMUser.email == payload["sub"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    logger.info(f"Аутентифицирован пользователь: {user.email}")
    return user


@router.post(
    "/register",
    response_model=User,
    status_code=201,
    summary="Регистрация нового пользователя",
    description="Регистрация нового пользователя с хешированием пароля",
)
async def register_user(
    user: UserCreate, db: AsyncSession = Depends(get_async_session)
):
    logger.info(f"Регистрация пользователя: {user.email}")
    stmt = select(ORMUser).where(ORMUser.email == user.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    logger.warning(f"Попытка регистрации уже существующего email: {user.email}")
    if existing_user:
        raise HTTPException(
            status_code=400, detail="Пользователь с таким email уже существует."
        )
    hashed_password = get_password_hash(user.password)
    db_user = ORMUser(name=user.name, email=user.email, password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    logger.info(f"Пользователь зарегистрирован: {db_user.email}")
    return db_user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=200,
    summary="Авторизация пользователя",
    description="Авторизация пользователя с проверкой пароля",
)
async def login_user(user: LoginRequest, db: AsyncSession = Depends(get_async_session)):
    logger.info(f"Авторизация пользователя: {user.email}")
    user = await check_login(user.email, user.password, db)
    token_payload = {
        "sub": user.email,
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    token = create_jwt_token(token_payload)
    logger.info(f"JWT токен создан для пользователя: {user.email}")

    return TokenResponse(access_token=token, token_type="bearer", expires_in=30 * 60)


@router.get(
    "/me",
    response_model=User,
    status_code=200,
    summary="Получение информации о текущем пользователе",
    description="Получение информации о текущем пользователе по токену",
)
async def get_current_user(
    current_user: ORMUser = Depends(get_current_user_from_token),
):
    logger.info(f"Получение текущего пользователя: {current_user.email}")
    return current_user
