from sqlmodel import Session, create_engine, select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import users as crud
from app.core.config import settings
from app.models import Users, Chats, UserChatParticipant, Message, MessageRead
from app.dto import UserCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

async_engine = create_async_engine(str(settings.SQLALCHEMY_ASYNC_DATABASE_URI))
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)
    group_chat_uuid = '44aca17a-7b10-4b06-828c-0a14f98de434'
    first_second_chat_uuid = '2d39f096-540b-41f9-a315-33269e915409'
    thrid_admin_chat_uuild = 'ab2ef4b0-7910-4991-88a2-86858afd169e'
    first_email = 'first@mail.ru'
    second_email = 'second@mail.ru'
    third_email = 'third@mail.ru'

    extra_user_data = [
        {
            'full_name': 'First User',
            'email': first_email,
            'password': settings.FIRST_SUPERUSER_PASSWORD,
            'is_superuser': False,
        },
        {
            'full_name': 'Second User',
            'email': second_email,
            'password': settings.FIRST_SUPERUSER_PASSWORD,
            'is_superuser': False,
        },
        {
            'full_name': 'Third User',
            'email': third_email,
            'password': settings.FIRST_SUPERUSER_PASSWORD,
            'is_superuser': False,
        },
        {
            'full_name': 'Admin User',
            'email': settings.FIRST_SUPERUSER,
            'password': settings.FIRST_SUPERUSER_PASSWORD,
            'is_superuser': True,
        }
    ]
    db_users = {
        first_email: None,
        second_email: None,
        third_email: None,
        settings.FIRST_SUPERUSER: None,
    }
    for value in extra_user_data:
        user = session.exec(
            select(Users).where(Users.email == value.get('email'))
        ).first()
        if not user:
            user_in = UserCreate(**value)
            user = crud.create_user(session=session, user_create=user_in)
        db_users[user.email] = user

    first_second_chat = session.exec(
        select(Chats).where(Chats.chat_id == first_second_chat_uuid)
    ).first()
    thrid_admin_chat = session.exec(
        select(Chats).where(Chats.chat_id == thrid_admin_chat_uuild)
    ).first()
    group_chat = session.exec(
        select(Chats).where(Chats.chat_id == group_chat_uuid)
    ).first()
    if not first_second_chat:
        first_second_chat = Chats(
            chat_id=first_second_chat_uuid,
            name=f'{db_users[first_email].full_name}_{db_users[second_email].full_name}',
            is_group=False,
            owner_id=db_users[first_email].id,
        )
        session.add(first_second_chat)
        session.commit()
        session.refresh(first_second_chat)
    if not thrid_admin_chat:
        thrid_admin_chat = Chats(
            chat_id=thrid_admin_chat_uuild,
            name=f'{db_users.get(settings.FIRST_SUPERUSER).full_name}_{db_users[third_email].full_name}',
            is_group=False,
            owner_id=db_users.get(settings.FIRST_SUPERUSER).id,
        )
        session.add(thrid_admin_chat)
        session.commit()
        session.refresh(thrid_admin_chat)
    if not group_chat:
        group_chat = Chats(
            chat_id=group_chat_uuid,
            name='Cool and Chill Chat',
            is_group=True,
            owner_id=db_users.get(settings.FIRST_SUPERUSER).id,
        )
        session.add(group_chat)
        session.commit()
        session.refresh(group_chat)

    first_participant = session.exec(
        select(UserChatParticipant).where(
            UserChatParticipant.chat_id == first_second_chat.id,
            UserChatParticipant.user_id == db_users.get(first_email).id
            )
    ).first()
    second_participant = session.exec(
        select(UserChatParticipant).where(
            UserChatParticipant.chat_id == first_second_chat.id,
            UserChatParticipant.user_id == db_users.get(second_email).id
            )
    ).first()
    thrid_participant = session.exec(
        select(UserChatParticipant).where(
            UserChatParticipant.chat_id == thrid_admin_chat.id,
            UserChatParticipant.user_id == db_users.get(third_email).id
            )
    ).first()
    admin_participant = session.exec(
        select(UserChatParticipant).where(
            UserChatParticipant.chat_id == thrid_admin_chat.id,
            UserChatParticipant.user_id == db_users.get(settings.FIRST_SUPERUSER).id
            )
    ).first()
    if not first_participant:
        first_participant = UserChatParticipant(
            chat_id=first_second_chat.id,
            user_id=db_users[first_email].id,
        )
        session.add(first_participant)
    if not second_participant:
        second_participant = UserChatParticipant(
            chat_id=first_second_chat.id,
            user_id=db_users[second_email].id,
        )
        session.add(second_participant)
    if not thrid_participant:
        thrid_participant = UserChatParticipant(
            chat_id=thrid_admin_chat.id,
            user_id=db_users[third_email].id,
        )
        session.add(thrid_participant)
    if not admin_participant:
        admin_participant = UserChatParticipant(
            chat_id=thrid_admin_chat.id,
            user_id=db_users[settings.FIRST_SUPERUSER].id,
        )
        session.add(admin_participant)

    messages = [
        'Привет!', 
        'Привет, как дела?', 
        'Делаю тестовое', 
        'И как?', 
        'Фронтенд это ад в аду.', 
        'Понимаю)',
    ]
    cnt = 0 
    chat_msg_data = [
        {
            'chat': first_second_chat,
            'users': [db_users[first_email], db_users[second_email]]
        },
        {
            'chat': thrid_admin_chat,
            'users': [db_users[third_email], db_users[settings.FIRST_SUPERUSER]],

        },
    ]

    for data in chat_msg_data:
        users = data.get('users')
        chat = data.get('chat')
        first_msg = session.exec(select(Message).where(
            Message.chat_id == chat.id,
        )).first()
        if not first_msg:
            for msg in messages:
                user = users[cnt]
                message = Message(
                    chat_id=chat.id,
                    sender_id=user.id,
                    content=msg,
                )
                session.add(message)
                session.commit()
                session.refresh(message)
                message_read = MessageRead(
                    message_id=message.id,
                    user_id=users[cnt ^ 1].id,
                )
                cnt = cnt ^ 1
                session.add(message_read)


    group_participant = session.exec(
        select(UserChatParticipant.user_id)
        .where(UserChatParticipant.user_id.in_(
            [u.id for u in db_users.values()]), 
            UserChatParticipant.chat_id == group_chat.id
            )
        ).all()
    for user in db_users.values():
        if user.id not in group_participant:
            session.add(UserChatParticipant(
                user_id=user.id,
                chat_id=group_chat.id,
            ))
    session.commit()
