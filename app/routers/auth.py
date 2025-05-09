from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db import get_db
from ..models.tables import User as ORMUser
from ..schemas.tables import UserCreate, User, UserLogin


router = APIRouter(
    tags=["auth"]
)

@router.post("/register",
            response_model=User,
            status_code=201,
            summary="Регистрация нового пользователя",
            description="Создание нового пользователя с уникальным именем и паролем.")
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):

    stmt = select(ORMUser).where(ORMUser.email == user.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует.")
    hashed_password = user.password
    db_user = ORMUser(
        name=user.name,
        email=user.email,
        password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post("/login",
            response_model=User)
async def login_user(user: UserLogin, db: AsyncSession = Depends(get_db)):

    stmt = select(ORMUser).where(ORMUser.email == user.email)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=400, detail="Пользователь не найден.")
    if db_user.password != user.password:
        raise HTTPException(status_code=400, detail="Неверный пароль.")
    return db_user