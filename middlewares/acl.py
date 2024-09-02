from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.models import User
from database.orm_query import orm_get_user, orm_add_user


class ACLMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],

    ) -> Any:
        user_from_event = data["event_from_user"]
        session = data["session"]
        user: User = await orm_get_user(session, user_from_event.id)
        if user is None:
            await orm_add_user(session, user_from_event.id)
            return await handler(event, data)
        elif not user.is_banned:
            return await handler(event, data)
        else:
            return
