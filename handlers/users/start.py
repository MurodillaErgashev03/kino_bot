from datetime import datetime

from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.inline.buttons import subscription_button
from loader import dp, db, bot
from aiogram import types

from utils.utils import is_admin


async def is_user_subscribed(user_id: int) -> bool:
    if await is_admin(user_id):
        return True  # Agar foydalanuvchi admin bo'lsa, True qaytaradi

    channels = db.get_all_channels()
    if not channels:
        return True

    for channel in channels:
        channel_id = channel['chat_id']
        try:
            chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if chat_member.status not in ['member', 'administrator', 'creator']:
                return False

        except TelegramBadRequest as e:
            print(f"Telegram xatosi: {e}")
            continue

        except Exception as e:
            print(f"Xato yuz berdi: {e}")
            continue

    return True


@dp.message(CommandStart())
async def start_bot(message: types.Message):
    user_id = message.from_user.id
    try:
        user = db.get_user(user_id=user_id)
        if not user:
            db.add_user(user_id=message.from_user.id, ban=0, sana=str(datetime.now()), status="1")
            print(f"Yangi foydalanuvchi qo'shildi: {user_id}")
        else:
            print(f"Foydalanuvchi allaqachon mavjud: {user}")
    except Exception as e:
        print(f"Foydalanuvchini qo'shishda xatolik: {e}")

    if await is_user_subscribed(user_id):
        msg = """👋 Salom 

Marhamat, kerakli kodni yuboring:"""
        chanel = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔎 Kodlarni qidirish", url="https://t.me/MeshpolvonFilm")]])
        await message.reply(msg, reply_markup=chanel)
    else:
        await message.answer(
            "⚠️ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling:",
            reply_markup=await subscription_button()
        )



@dp.callback_query(lambda c: c.data == "subscribe_true")
async def oldim(call: types.CallbackQuery):
    await call.message.delete()
    if await is_user_subscribed(call.from_user.id):
        msg = """👋 Salom 

        Marhamat, kerakli kodni yuboring:"""
        chanel = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔎 Kodlarni qidirish", url="https://t.me/MeshpolvonFilm")]])
        await call.message.answer(msg, reply_markup=chanel)
    else:
        await call.message.answer("Iltimios! ⚠️ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling:",
                                  reply_markup=await subscription_button())
