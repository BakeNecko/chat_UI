import asyncio
import json
import logging
from app.crud.groups import get_user_chats
from app.crud.messages import create_group_msg, create_lc_msg, get_msg_by_id, get_msg_by_uuid
from app.dto.chatmsg import MessageDTO, MessagePublic
from app.utils import WsCloseCode, async_task_graceful_shutdown
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException
from app.api.deps import (
    SessionAsyncDep,
    SessionDep,
    get_current_user,
)
from fastapi.websockets import WebSocketState
from sqlmodel import select

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/chat")
async def ws_chat(
    websocket: WebSocket,
    session: SessionDep,
    async_session: SessionAsyncDep,
):
    await websocket.accept()

    pubsub = websocket.app.state.redis_client.pubsub(
        ignore_subscribe_messages=True)
    is_init = False
    user_id = None
    receive_task = None
    ws_close_status = WsCloseCode.NORMAL_CLOSURE
    message_queue = asyncio.Queue()

    # Log context
    socket_id = id(websocket)
    client_host = websocket.client.host if websocket.client else "unknown"

    def log_info(msg, **kwargs):
        base = {'socket_id': socket_id,
                'client_host': client_host, 'user_id': user_id}
        base.update(kwargs)
        logger.info(f"{msg} | context: {base}")

    def log_warning(msg, **kwargs):
        base = {'socket_id': socket_id,
                'client_host': client_host, 'user_id': user_id}
        base.update(kwargs)
        logger.warning(f"{msg} | context: {base}")

    def log_error(msg, **kwargs):
        base = {'socket_id': socket_id,
                'client_host': client_host, 'user_id': user_id}
        base.update(kwargs)
        logger.error(f"{msg} | context: {base}")

    async def receive_messages():
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
                if message and message.get('data'):
                    await message_queue.put(message['data'].decode())
                else:
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            log_info("Receive messages task cancelled")
            raise
        except Exception as e:
            log_error(f"Error in receive_messages: {e}")

    async def send_messages():
        try:
            while True:
                message = await message_queue.get()
                try:
                    await websocket.send_text(message)
                except WebSocketDisconnect:
                    log_info("WebSocket client disconnected")
                    break
                except Exception as send_exc:
                    log_error(
                        f"Failed to send message to websocket: {send_exc}")
                    break
        except asyncio.CancelledError:
            log_info("Send messages task cancelled")
            raise
        except Exception as e:
            log_error(f"Error in send_messages: {e}")

    try:
        while True:
            data = await websocket.receive_text()
            msg_dto = MessageDTO(**json.loads(data))

            if msg_dto.is_init:
                user = get_current_user(session, msg_dto.content)
                user_id = user.id

                group_chats = await get_user_chats(
                    async_session=async_session,
                    user_id=user_id,
                    is_group=True,
                )
                channels = [*[str(i.chat_id)
                              for i in group_chats], f'lc_chat_{user_id}']
                await pubsub.subscribe(*channels)
                log_info("Subscribed to channels", channels=channels)

                receive_task = asyncio.create_task(receive_messages())
                send_task = asyncio.create_task(send_messages())
                is_init = True
                continue

            if not is_init:
                ws_close_status = WsCloseCode.POLICY_VIOLATION
                raise WebSocketException(
                    'WebSocket is not initialized with user')

            exist_msg = await get_msg_by_uuid(async_session=async_session, msg_uuid=msg_dto.message_uuid)
            if exist_msg:
                log_warning(
                    f'Attempt to send an existing message',
                    msg_id=exist_msg.id,
                    msg_uuid=exist_msg.message_uuid,
                )
                continue

            if msg_dto.is_lc:
                msg = await create_lc_msg(
                    async_session=async_session,
                    sender_id=user_id,
                    receiver_id=msg_dto.receiver_id,
                    message=msg_dto.content,
                )
                publish_channel = f"lc_chat_{msg_dto.receiver_id}"
            elif msg_dto.is_group:
                msg = await create_group_msg(
                    async_session=async_session,
                    sender_id=user_id,
                    chat_uuid=msg_dto.receiver_id,
                    message=msg_dto.content,
                )
                publish_channel = msg_dto.receiver_id
            else:
                ws_close_status = WsCloseCode.UNSUPPORTED_DATA
                raise WebSocketException(
                    f'Undefined message type: {msg_dto.type} content: {msg_dto.content}'
                    )

            updated_msg = await get_msg_by_id(async_session=async_session, msg_id=msg.id)
            msg_dict = MessagePublic.model_validate(updated_msg).model_dump()
            msg_dict['updated_at'] = msg_dict['updated_at'].isoformat()

            await websocket.app.state.redis_client.publish(
                publish_channel,
                json.dumps(msg_dict),
            )
            log_info(
                f"Published message to channel {publish_channel}", message=msg_dict,
                )
    except Exception as exc:
        log_error(f"Unexpected error in websocket: {exc}")
        ws_close_status = WsCloseCode.INTERNAL_SERVER_ERROR
    finally:
        if receive_task:
            await async_task_graceful_shutdown(receive_task)
        if send_task:
            await async_task_graceful_shutdown(send_task)

        try:
            await pubsub.unsubscribe()
        except Exception as e:
            log_error(f"Failed to unsubscribe from channels: {e}")

        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(ws_close_status)
