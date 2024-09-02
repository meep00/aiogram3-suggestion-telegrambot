from aiogram.filters import BaseFilter
from aiogram.types import Message

from config import ADMIN_USER_ID


class AdminFilter(BaseFilter):
    is_admin: bool = True

    async def __call__(self, obj: Message) -> bool:
        return (obj.from_user.id == int(ADMIN_USER_ID)) == self.is_admin
