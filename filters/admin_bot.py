from aiogram.filters import Filter
from aiogram import types

from loader import db

class IsBotAdmin(Filter):
    async def __call__(self, message: types.Message) -> bool:
        admins = db.get_all_admins()
        return str(message.from_user.id) in [str(admin['user_id']) for admin in admins]
