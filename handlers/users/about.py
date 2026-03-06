from aiogram.filters import Command
from aiogram import types

from handlers.users import user_router


@user_router.message(Command('about'))
async def about_bot(message: types.Message):
    await message.answer(f"MeshpolvonFilm Bot -  orqali siz o'zingizga yoqqan kinoni topishingiz mumkin 🎬 !\n")
