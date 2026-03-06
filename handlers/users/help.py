from aiogram.filters import Command
from aiogram import types

from handlers.users import user_router


@user_router.message(Command('help'))
async def help_bot(message: types.Message):
    await message.answer(
        f"Qanday yordam kerak?\n"
        f"Asosiy buyruqlar:\n"
        f"/start - botni ishga tushurish\n"
        f"/help"
    )
