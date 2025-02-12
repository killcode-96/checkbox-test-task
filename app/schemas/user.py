import uuid
from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    username: str
    full_name: str | None = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class User(UserBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
