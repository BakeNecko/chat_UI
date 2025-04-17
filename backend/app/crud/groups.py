from uuid import UUID
from app.models.chatmsg import Chats, UserChatParticipant
from app.models.users import Users
from sqlalchemy import and_, func
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import subqueryload


async def get_user_chats(
    *,
    async_session: AsyncSession,
    user_id: int,
    is_group: bool = None,
    id_only: bool = False,
    with_FK: bool = True,
) -> list[Chats]:
    if id_only:
        base_statement = select(Chats.id)
    else:
        base_statement = select(Chats)

    base_statement = base_statement.join(
        UserChatParticipant,
        UserChatParticipant.chat_id == Chats.id,
    ).where(
        UserChatParticipant.user_id == user_id,
    )

    if is_group is not None:
        base_statement = base_statement.where(
            Chats.is_group == is_group
        )

    if not id_only and with_FK:
        base_statement = base_statement.options(selectinload(Chats.users))

    return (await async_session.execute(base_statement)).scalars().all()


def _get_chat_statement(
    only_id: bool = True,
    with_FK: bool = True,
):
    if only_id:
        base_statement = select(Chats.id)
    else:
        base_statement = select(Chats)
    if not only_id and with_FK:
        base_statement = base_statement.join(
            UserChatParticipant,
            UserChatParticipant.chat_id == Chats.id,
        ).options(selectinload(Chats.users))
    return base_statement


async def get_chat_from_id(
    *,
    async_session: AsyncSession,
    chat_id: int,
    with_FK: bool = True,
) -> int | Chats | None:
    statement = _get_chat_statement(False, with_FK).where(Chats.id == chat_id)
    return (await async_session.execute(statement)).scalars().first()


async def get_chat_from_uuid(
    *,
    async_session: AsyncSession,
    chat_uuid: str | UUID,
    only_id: bool = True,
    with_FK: bool = True,
) -> int | Chats | None:
    statement = _get_chat_statement(only_id, with_FK)

    chat_uuid_str = str(chat_uuid) if isinstance(
        chat_uuid, UUID) else chat_uuid
    statement = statement.where(Chats.chat_id == chat_uuid_str)

    return (await async_session.execute(statement)).scalars().first()


async def count_users_by_ids(*, async_session: AsyncSession, user_ids: list[int]) -> int:
    return (await async_session.execute(
        select(func.count()).where(Users.id.in_(user_ids))
    )).scalar()


async def create_group(
        *,
        async_session: AsyncSession,
        chat_name: str,
        is_group: bool,
        owner_id: int,
) -> Chats:
    new_group = Chats(
        name=chat_name,
        is_group=is_group,
        owner_id=owner_id,
    )
    async_session.add(new_group)
    await async_session.commit()
    await async_session.refresh(new_group)
    return new_group


async def add_participant_to_group(
    *,
    async_session: AsyncSession,
    user_ids: list[int],
    group_id: int,
):
    for user_id in user_ids:
        participant = UserChatParticipant(chat_id=group_id, user_id=user_id)
        async_session.add(participant)
    await async_session.commit()


async def find_lc_group(
    *,
    async_session: AsyncSession,
    user_1_id: int,
    user_2_id: int,
) -> Chats | None:
    state = (
        select(Chats)
        .join(UserChatParticipant)
        .group_by(Chats.id)
        .having(
            and_(
                func.count(UserChatParticipant.user_id) == 2,
                func.bool_and(UserChatParticipant.user_id.in_(
                    [user_1_id, user_2_id])),
                Chats.is_group == False
            )
        )
    )
    return (await async_session.execute(state)).scalars().first()


async def get_user_participant_chat(*, async_session: AsyncSession, user_id: int, chat_id: int) -> UserChatParticipant | None:
    return (
        await async_session.execute(
            select(UserChatParticipant)
            .where(
                UserChatParticipant.chat_id == chat_id,
                UserChatParticipant.user_id == user_id
            ))
    ).scalars().first()


async def get_users_groups(*, async_session: AsyncSession, user_id: int, is_group: bool = None):
    statement = (
        select(Chats)
        .options(subqueryload(Chats.users))
        .join(
            UserChatParticipant,
            UserChatParticipant.chat_id == Chats.id,
        )
        .where(UserChatParticipant.user_id == user_id)
    )
    if is_group is not None:
        statement = statement.where(Chats.is_group == is_group)
    return (await async_session.execute(statement)).scalars().all()
