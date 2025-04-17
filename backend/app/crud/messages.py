
from app.models.chatmsg import Message
from fastapi import HTTPException

from sqlmodel import func, select
from sqlalchemy.orm import selectinload, subqueryload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel.sql.expression import SelectOfScalar

from app.models import Chats, UserChatParticipant, Message, MessageRead
from .groups import get_chat_from_uuid


def add_FK_for_msg(state: SelectOfScalar) -> SelectOfScalar:
    return state.options(selectinload(Message.chat), selectinload(Message.sender), subqueryload(Message.read_by_users))


async def get_msg_by_id(
    *,
    async_session: AsyncSession,
    msg_id: str,
    with_FK: bool = True,
) -> Message | None:
    state = select(Message).where(Message.id == msg_id)
    if with_FK:
        state = add_FK_for_msg(state)
    return (await async_session.execute(state)).scalars().first()


async def get_msg_by_uuid(
    *,
    async_session: AsyncSession,
    msg_uuid: str,
    with_FK: bool = True,
) -> Message | None:
    state = select(Message).where(Message.message_uuid == msg_uuid)
    if with_FK:
        state = add_FK_for_msg(state)
    return (await async_session.execute(state)).scalars().first()


async def create_lc_msg(*, async_session: AsyncSession, sender_id, receiver_id, message: str) -> Message:
    chat_id = (await async_session.execute(
        select(Chats.id)
        .join(UserChatParticipant)
        .where(
            Chats.is_group == False,
            UserChatParticipant.user_id.in_([sender_id, receiver_id])
        )
        .group_by(Chats.id)
        .having(func.count(UserChatParticipant.user_id) == 2)
    )).scalars().first()

    if not chat_id:
        raise HTTPException(
            detail=f'LC-Chat not found for Users: {sender_id, receiver_id}',
            status_code=400,
        )

    db_obj = Message(
        chat_id=chat_id,
        sender_id=sender_id,
        content=message,
    )
    async_session.add(db_obj)
    await async_session.commit()
    await async_session.refresh(db_obj)
    return db_obj


async def create_group_msg(*, async_session: AsyncSession, chat_uuid: str, sender_id: int, message: str) -> Message:
    chat_id = await get_chat_from_uuid(
        async_session=async_session,
        chat_uuid=chat_uuid,
        only_id=True,
    )
    db_obj = Message(
        chat_id=chat_id,
        sender_id=sender_id,
        content=message,
    )
    async_session.add(db_obj)
    await async_session.commit()
    await async_session.refresh(db_obj)
    return db_obj


async def get_unread_msg(*, async_session: AsyncSession, chat_id: int, user_id: int) -> Message:
    return (await async_session.execute(
        select(Message)
        .where(
            Message.chat_id == chat_id,
            Message.sender_id != user_id,
            ~Message.read_by_users.any(id=user_id)
        )
    )).scalars().all()


async def set_read_msg_by_user(
    *,
    async_session: AsyncSession,
    user_id: int,
    msg_id: int,
):
    message_read = MessageRead(message_id=msg_id, user_id=user_id)
    async_session.add(message_read)
    await async_session.commit()


async def get_msg_for_chat(
        *,
        async_session: AsyncSession,
        chat_id: int,
        limit: int = None,
        offset: int = None,
):
    statement = (
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at, Message.id)
    )
    statement = add_FK_for_msg(statement)
    if limit:
        statement = statement.limit(limit)
    if offset is not None:
        statement = statement.offset(offset)

    return (await async_session.execute(statement)).scalars().all()
