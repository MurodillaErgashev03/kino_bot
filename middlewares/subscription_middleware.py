import time
from datetime import datetime
from typing import Any, Awaitable, Callable, cast, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, InlineKeyboardMarkup, InlineKeyboardButton, \
    Message  # Message ni import qildik

# get_unsubscribed_channels ni import qilamiz
from handlers.users.start import get_unsubscribed_channels

from loader import db, bot  # bot ni ham import qilamiz, chunki get_unsubscribed_channels uni ishlatadi


# from aiogram import types - types ni o'rniga Message ni import qildik

class UserCheckMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        # Update obyektini Message obyektiga aylantirishga urinish
        # Chunki bizga event.message kerak. Agar event Message emas, boshqa tur bo'lsa (masalan, CallbackQuery),
        # bu yerda xatolik bo'lmasligi uchun tekshiramiz.
        message = event.message  # Message obyektini to'g'ridan-to'g'ri event.message dan olamiz

        if not message:  # Agar xabar mavjud bo'lmasa (masalan, bu callback_query bo'lsa), keyingi handlerga o'tamiz
            return await handler(event, data)

        user_id = message.from_user.id

        # 1. Foydalanuvchini bazaga saqlash/yangilash mantig'i
        try:
            user = db.get_user(user_id=user_id)
            if not user:
                # user_id ni str ga o'tkazganingizga ishonch hosil qiling
                db.add_user(user_id=str(user_id), ban=0, sana=str(datetime.now()), status="1")
                print(f"Yangi foydalanuvchi qo'shildi: {user_id}")
            else:
                # Agar foydalanuvchi allaqachon mavjud bo'lsa
                # Printda user obyektini to'g'ri chiqarish uchun .get() dan foydalanish
                print(f"Foydalanuvchi allaqachon mavjud: {user.get('user_id')}")
        except Exception as e:
            print(f"Foydalanuvchini qo'shish/tekshirishda xatolik (middleware): {e}")

        # 2. Obuna holatini tekshirish mantig'i
        unsubscribed_channels = await get_unsubscribed_channels(user_id)

        if unsubscribed_channels:  # Agar ro'yxat bo'sh bo'lmasa, demak obuna bo'lishi kerak
            subscribe_buttons = []
            for i, channel_info in enumerate(unsubscribed_channels):
                channel_name = f"{i + 1}-kanal"
                if channel_info.get('url') and channel_info['url'] != '#':  # .get() bilan url ni olish
                    subscribe_buttons.append([InlineKeyboardButton(text=channel_name, url=channel_info['url'])])
                else:
                    subscribe_buttons.append([InlineKeyboardButton(text=channel_name,
                                                                   callback_data=f"check_channel_{channel_info['chat_id']}")])

            subscribe_buttons.append([InlineKeyboardButton(text="Obuna bo'ldim ✅", callback_data="subscribe_true")])

            await message.answer(  # event.message o'rniga to'g'ridan-to'g'ri message dan foydalanamiz
                "⚠️ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling (agar maxfiy kanal bo'lsa, qo'shilish so'rovini yuboring):",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=subscribe_buttons)
            )
            return  # Agar obuna bo'lmagan bo'lsa, keyingi handlerga o'tishni to'xtatamiz

        return await handler(event, data)