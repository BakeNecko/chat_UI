
from app.models.base import BaseTSIDModel
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from typing import TYPE_CHECKING, List
from .chatmsg import UserChatParticipant, MessageRead

if TYPE_CHECKING:
    from .chatmsg import Message, Chats


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class Users(BaseTSIDModel, UserBase, table=True):
    __tablename__ = "users"

    hashed_password: str
    send_messages: List["Message"] = Relationship(
        back_populates="sender",
        cascade_delete=True,
    )
    chats: List["Chats"] = Relationship(
        back_populates="users", link_model=UserChatParticipant,
    )
    read_messages: List["Message"] = Relationship(
        back_populates="read_by_users",
        link_model=MessageRead,
    )
    own_chats: List["Chats"] = Relationship(
        back_populates="owner",
    )

    @property
    def get_name(self):
        return self.full_name if self.full_name else self.email
