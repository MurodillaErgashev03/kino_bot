from aiogram.filters import Command
from loader import dp
from aiogram import types


@dp.message(Command('about'))
async def help_bot(message: types.Message):
    await message.answer(f"MeshpolvonFilm Bot -  orqali siz o'zingizga yoqqan kinoni topishingiz mumkin 🎬 !\n")


