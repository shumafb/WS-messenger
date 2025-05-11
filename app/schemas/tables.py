from datetime import datetime, timezone
from enum import Enum

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
    text: str = Field(..., min_length=1, max_length=500)
    chat_id: int
    sender_id: int


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    timestamp: datetime = Field(default_factory=datetime.now(timezone.utc))
    is_read: bool = Field(default=False)

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message_id: int
    sender_id: int
    text: str
    timestamp: str
    is_read: bool
    client_message_id: str | None

    class Config:
        from_attributes = True
