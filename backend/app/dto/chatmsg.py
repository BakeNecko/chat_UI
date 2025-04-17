from datetime import datetime
from typing import List, Literal, Optional
from sqlmodel import Field, SQLModel
from uuid import UUID
from .users import UserShort


class GroupCreate(SQLModel):
    name: str = Field(..., description="Название группового чата")
    user_ids: List[int] = Field(
        ..., description="Список ID пользователей, которые будут добавлены в группу")


class GroupPublic(SQLModel):
    id: int = Field(..., description="Уникальный идентификатор группового чата")
    chat_id: str = Field(...,
                         description="Уникальный идентификатор группового чата")
    name: str = Field(..., description="Название группового чата")
    user_ids: List[int] = Field(...,
                                description="Список ID пользователей в группе")
    owner_id: int = Field(...,
                          description="ID пользователя, который создал группу")


class ChatsPublic(SQLModel):
    id: int
    chat_id: UUID = Field(..., description="Уникальный идентификатор чата")
    name: str = Field(..., description="Название чата")
    is_group: bool = Field(...,
                           description="Указывает, является ли этот чат групповым")
    owner_id: int = Field(...,
                          description="ID пользователя, который владеет этим чатом")
    users: List[UserShort]
    owner: UserShort


class MyChatsPublic(SQLModel):
    group_chats: List[ChatsPublic]
    lc_chats: List[ChatsPublic]


class MessageDTO(SQLModel):
    receiver_id: str | int = Field(None)
    content: str
    type: Literal['lc', 'group', 'init']
    message_uuid: str | UUID = Field(None)

    @property
    def is_init(self):
        return self.type == 'init'

    @property
    def is_lc(self) -> bool:
        return self.type == 'lc'

    @property
    def is_group(self) -> bool:
        return self.type == 'group'


class MessagePublic(SQLModel):
    id: int
    chat_id: int
    sender_id: int
    content: str
    read_by_users: List[UserShort] = []
    sender: UserShort
    updated_at: datetime


class NotifyMsg(SQLModel):
    type: Literal['MSG_READ', 'CHAT_INVITED']
    meta_data: dict
    content: str
