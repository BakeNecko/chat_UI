import uuid
from typing import TYPE_CHECKING, List
from app.models.base import BaseTSIDModel, BaseTSModel
from sqlalchemy import UniqueConstraint
from sqlmodel import (
    Field,
    Index,
    Relationship,
    SQLModel,
)

if TYPE_CHECKING:
    from .users import Users


class UserChatParticipant(BaseTSModel, SQLModel, table=True):
    __tablename__ = 'user_chat_participants'

    chat_id: int = Field(foreign_key="chats.id", primary_key=True)
    user_id: int = Field(foreign_key="users.id", primary_key=True)


class Chats(BaseTSIDModel, SQLModel, table=True):
    __tablename__ = "chats"

    name: str = Field(min_length=1, max_length=255,
                      default=None, nullable=True)
    chat_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    is_group: bool = Field(default=False)
    owner_id: int = Field(foreign_key="users.id")
    owner: "Users" = Relationship(back_populates="own_chats")

    users: List["Users"] = Relationship(
        back_populates="chats",
        link_model=UserChatParticipant
    )

    messages: List["Message"] = Relationship(
        back_populates="chat", cascade_delete=True)

    # experiment for personal needs
    __table_args__ = (
        Index(
            'uq_chat_name_is_group_false',
            'name',
            postgresql_where=(is_group == False),
            unique=True
        ),
    )


class MessageRead(BaseTSModel, SQLModel, table=True):
    __tablename__ = "message_read"

    message_id: int = Field(foreign_key="message.id", primary_key=True)
    user_id: int = Field(foreign_key="users.id", primary_key=True)


class Message(BaseTSIDModel, SQLModel, table=True):
    __tablename__ = "message"

    message_uuid: uuid.UUID = Field(default_factory=uuid.uuid4)

    chat_id: int = Field(foreign_key="chats.id", ondelete="CASCADE")
    chat: "Chats" = Relationship(back_populates="messages")

    sender_id: int = Field(foreign_key="users.id")
    sender: "Users" = Relationship(back_populates="send_messages")

    read_by_users: List["Users"] = Relationship(
        back_populates="read_messages",
        link_model=MessageRead,
    )

    content: str = Field(max_length=2048)

    __table_args__ = (
        UniqueConstraint("message_uuid", name="uq_message_message_uuid"),
    )
