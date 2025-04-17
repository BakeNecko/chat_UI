import json
from typing import List
from app.crud.groups import get_chat_from_id, get_user_participant_chat
from app.crud.messages import get_msg_by_id, get_msg_for_chat, get_unread_msg, set_read_msg_by_user
from app.dto.chatmsg import MessagePublic, NotifyMsg
from app.dto.users import UserShort
from app.models.users import Users
from fastapi import APIRouter, HTTPException, Request

from app.api.deps import (
    CurrentUser,
    SessionDep,
    SessionAsyncDep,
)
from app.models import Message
from sqlalchemy.exc import IntegrityError
from redis.asyncio import Redis

router = APIRouter(prefix="/msg", tags=["msg"])


async def _send_msg_read_notify(msg: Message, who_read: Users, redis_client: Redis) -> int:
    msg_content = msg.content
    if len(msg_content) > 50:
        msg_content = msg_content[:50] + '...'

    payload = NotifyMsg(
        type='MSG_READ',
        meta_data={
            'msg_id': msg.id,
            'who_read': UserShort.model_validate(who_read).model_dump_json()
        },
        content=f'Ваше сообщение: "{msg_content}" прочитанно пользователем: "{who_read.get_name}"\n',
    )
    return await redis_client.publish(
        f'lc_chat_{msg.sender_id}',
        json.dumps(payload.model_dump_json()),
    )


@router.get("/mark_msg_read/{msg_id}")
async def mark_msg_read(
    msg_id: int,
    request: Request,
    async_session: SessionAsyncDep,
    current_user: CurrentUser,
):
    msg = await get_msg_by_id(async_session=async_session, msg_id=msg_id)
    if not msg:
        raise HTTPException(detail='Message not found', status_code=404)
    chat = await get_chat_from_id(async_session=async_session, chat_id=msg.chat_id)
    if current_user not in chat.users:
        raise HTTPException(detail='Object Permission Denied', status_code=403)
    if msg.sender_id == current_user.id:
        raise HTTPException(
            detail='Y cant read youself message!', status_code=400)
    if current_user in msg.read_by_users:
        raise HTTPException(
            detail='Y already read this message!', status_code=400)
    await set_read_msg_by_user(
        async_session=async_session,
        msg_id=msg_id,
        user_id=current_user.id,
    )
    await _send_msg_read_notify(msg, current_user, request.app.state.redis_client)


@router.get("/history/{chat_id}", response_model=List[MessagePublic])
async def chat_msg_history(
    chat_id: int,
    request: Request,
    async_session: SessionAsyncDep,
    current_user: CurrentUser,
    limit: int = 100,
    offset: int = 0,
):
    user_participant = await get_user_participant_chat(
        async_session=async_session,
        chat_id=chat_id,
        user_id=current_user.id,
    )
    if not user_participant:
        raise HTTPException(
            detail='You are not a member of this chat', status_code=403)

    unread_messages = await get_unread_msg(async_session=async_session, user_id=current_user.id, chat_id=chat_id)
    # кнш лучше отправить пачкой, но я не знаю как их обработать на фронте по христиански
    for message in unread_messages:
        await set_read_msg_by_user(
            async_session=async_session,
            msg_id=message.id,
            user_id=current_user.id,
        )
        await _send_msg_read_notify(message, current_user, request.app.state.redis_client)

    return await get_msg_for_chat(
        async_session=async_session,
        chat_id=chat_id,
        limit=limit,
        offset=offset
    )
