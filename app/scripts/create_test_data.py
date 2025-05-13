import asyncio
from datetime import datetime, timedelta

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from app.db import SQLALCHEMY_DATABASE_URL
from app.models.tables import User, Chat, Message, chat_users, Group, group_members

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_data():
    async with async_session() as session:
        users_data = [
            {"name": "Алиса", "email": "alice@example.com", "password": pwd_context.hash("password123")},
            {"name": "Боб", "email": "bob@example.com", "password": pwd_context.hash("password123")},
            {"name": "Чарли", "email": "charlie@example.com", "password": pwd_context.hash("password123")},
            {"name": "Дэвид", "email": "david@example.com", "password": pwd_context.hash("password123")},
        ]
        result = await session.execute(insert(User).returning(User), users_data)
        users = result.scalars().all()
        
        private_chat = Chat(name="Алиса и Боб", chat_type="private")
        session.add(private_chat)
        await session.flush()
        
        private_chat_users = [
            {"chat_id": private_chat.id, "user_id": users[0].id},
            {"chat_id": private_chat.id, "user_id": users[1].id},
        ]
        await session.execute(insert(chat_users), private_chat_users)
        
        group_chat = Chat(name="Команда проекта", chat_type="group")
        session.add(group_chat)
        await session.flush()
        
        group = Group(
            chat_id=group_chat.id,
            name="Команда проекта",
            creator_id=users[0].id
        )
        session.add(group)
        await session.flush()
        
        group_chat_users = [
            {"chat_id": group_chat.id, "user_id": user.id}
            for user in users
        ]
        await session.execute(insert(chat_users), group_chat_users)
        
        group_members_data = [
            {"group_id": group.id, "user_id": user.id}
            for user in users
        ]
        await session.execute(insert(group_members), group_members_data)
        
        private_messages = [
            Message(
                text=f"Тестовое сообщение {i}",
                chat_id=private_chat.id,
                sender_id=users[i % 2].id,
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                created_at=datetime.utcnow() - timedelta(minutes=i)
            )
            for i in range(10)
        ]
        session.add_all(private_messages)
        
        group_messages = [
            Message(
                text=f"Групповое сообщение {i}",
                chat_id=group_chat.id,
                sender_id=users[i % len(users)].id,
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                created_at=datetime.utcnow() - timedelta(minutes=i)
            )
            for i in range(15)
        ]
        session.add_all(group_messages)
        
        await session.commit()

if __name__ == "__main__":
    asyncio.run(create_test_data())