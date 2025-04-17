from fastapi import APIRouter

from app.api.routes import login, private, users, utils, groups, ws_chats, msg
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(groups.router)
api_router.include_router(ws_chats.router)
api_router.include_router(msg.router)

# api_router.include_router(items.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
