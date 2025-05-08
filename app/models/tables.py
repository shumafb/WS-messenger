from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Table, Enum
from sqlalchemy.orm import relationship
from app.db import Base


group_members = Table(
    'group_members', Base.metadata,
    Column('group_id', ForeignKey('groups.id'), primary_key=True),
    Column('user_id', ForeignKey('users.id'), primary_key=True),
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    email = Column(String(50), unique=True, index=True)
    password = Column(String)

    groups = relationship("Group", secondary=group_members, back_populates="members")
    messages = relationship("Message", back_populates="sender", cascade="all, delete-orphan")

class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    chat_type = Column(Enum('private', 'group', name='chat_type'), default='private', index=True)

    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    creator_id = Column(Integer, ForeignKey('users.id'))

    members = relationship("User", secondary=group_members, back_populates="groups")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    sender_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime(timezone=True),  index=True)
    is_read = Column(Boolean, default=False)

    sender = relationship("User", back_populates="messages")
    chat = relationship("Chat", back_populates="messages")