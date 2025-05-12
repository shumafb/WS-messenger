from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db import Base


group_members = Table(
    "group_members",
    Base.metadata,
    Column("group_id", ForeignKey("groups.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

    groups = relationship("Group", secondary=group_members, back_populates="members")
    messages = relationship(
        "Message", back_populates="sender", cascade="all, delete-orphan"
    )


class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    chat_type = Column(Enum("private", "group", name="chat_type"), default="private")

    messages = relationship(
        "Message", back_populates="chat", cascade="all, delete-orphan"
    )


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    creator_id = Column(Integer, ForeignKey("users.id"))

    members = relationship("User", secondary=group_members, back_populates="groups")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True))
    client_message_id = Column(String, unique=True, nullable=True, index=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", back_populates="messages")
    chat = relationship("Chat", back_populates="messages")
