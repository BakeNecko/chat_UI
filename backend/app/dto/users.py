import uuid
from app.models import UserBase
from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class UserShort(SQLModel):
    id: int
    email: EmailStr
    full_name: str | None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(
        default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)

# Properties to return via API, id is always required


class UserPublic(UserBase):
    id: str | int


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int

# Generic message


class Message(SQLModel):
    message: str
