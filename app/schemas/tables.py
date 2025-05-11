from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ChatType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"


class UserEmail(BaseModel):
    email: EmailStr


class UserBase(UserEmail):
    name: str = Field(..., min_length=1, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=64)


class UserLogin(UserEmail):
    password: str = Field(..., min_length=8, max_length=64)


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class ChatBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    chat_type: ChatType = Field(default=ChatType.PRIVATE)


class ChatCreate(ChatBase):
    pass


class Chat(ChatBase):
    id: int

    class Config:
        from_attributes = True


class GroupBase(ChatBase):
    name: str = Field(..., min_length=1, max_length=50)
    creator_id: int


class GroupCreate(GroupBase):
    pass


class Group(GroupBase):
    id: int
    members: list[User] = Field(default_factory=list)

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    text: str
    chat_id: int
    client_message_id: Optional[str] = None


class MessageCreate(MessageBase):
    sender_id: int


class Message(MessageBase):
    id: int
    sender_id: int
    created_at: datetime

    class Config:
        from_attributes = True