from typing import Any
from app.crud.groups import add_participant_to_group, count_users_by_ids, create_group, find_lc_group, get_users_groups
from app.dto.chatmsg import MyChatsPublic
from fastapi import APIRouter, HTTPException

from app.api.deps import (
    CurrentUser,
    SessionAsyncDep,
)
from app.dto import GroupCreate
from app.models import Chats

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post(
    "/create",
    status_code=201,
)
async def group_create(
    group_data: GroupCreate,
    current_user: CurrentUser,
    async_session: SessionAsyncDep,
) -> Any:
    if current_user.id in group_data.user_ids:
        # Обычно такие места подвергаются доп. логированию
        # Как попытка поломать бэк. 3 стрйка -> Бан по fingerprint'y
        raise HTTPException(
            status_code=400,
            detail="You cant select youself as chat participant."
        )
    cnt_users = await count_users_by_ids(
        async_session=async_session,
        user_ids=group_data.user_ids,
    )
    print('cnt_users: ', cnt_users)
    print('users: ', group_data.user_ids)
    if len(group_data.user_ids) != cnt_users:
        raise HTTPException(
            status_code=400, detail="One or more users not found.")
    if cnt_users == 1:
        exist_group = await find_lc_group(
            async_session=async_session,
            user_1_id=current_user.id,
            user_2_id=group_data.user_ids[0],
        )
        if exist_group:
            raise HTTPException(
                status_code=400,
                detail="You already have a private chat with this user",
            )
    new_group = await create_group(
        async_session=async_session,
        chat_name=group_data.name,
        is_group=True if cnt_users >= 2 else False,
        owner_id=current_user.id
    )
    group_data.user_ids.append(current_user.id)
    await add_participant_to_group(
        async_session=async_session,
        user_ids=group_data.user_ids,
        group_id=new_group.id
    )


@router.delete("/delete")
async def delete_group(
    chat_id: int,
    current_user: CurrentUser,
    async_session: SessionAsyncDep,
) -> Any:
    chat = await async_session.get(Chats, chat_id)

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found.")
    if chat.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this group.")

    await async_session.delete(chat)
    await async_session.commit()


@router.get("/my", response_model=MyChatsPublic)
async def my_chats(
    current_user: CurrentUser,
    async_session: SessionAsyncDep,
):
    return MyChatsPublic(
        group_chats=(await get_users_groups(async_session=async_session, user_id=current_user.id, is_group=True)),
        lc_chats=(await get_users_groups(async_session=async_session, user_id=current_user.id, is_group=False)),
    )
