from datetime import datetime
from enum import Enum
from typing import List, Optional

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
    name: str = Field(None, min_length=1, max_length=50)
    chat_type: ChatType = Field(default=ChatType.PRIVATE)


class ChatCreate(ChatBase):
    member_ids: List[int]


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


class MessageCreate(BaseModel):
    text: str
    client_message_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "text": "Привет",
                "client_message_id": "e7b8f9a2-1c4d-4a3f-bd2c-1234567890ab",
            }
        }


class Message(MessageBase):
    id: int
    sender_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageHistoryResponse(BaseModel):
    items: List[Message]
    total: int
    offset: int
    limit: int

    class Config:
        from_attributes = True
