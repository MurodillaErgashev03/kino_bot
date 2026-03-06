from datetime import datetime
from typing import Any, Awaitable, Callable, Dict
from aiogram.enums import ChatType

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, InlineKeyboardMarkup, InlineKeyboardButton

from handlers.users.start import get_unsubscribed_channels
from loader import db


class UserCheckMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        message = event.message
        if not message:
            return await handler(event, data)

        if message.chat.type != ChatType.PRIVATE:
            return

        user_id = message.from_user.id

        try:
            user = db.get_user(user_id=user_id)
            if not user:
                db.add_user(user_id=str(user_id), ban=0, sana=str(datetime.now()), status="1")
        except Exception as e:
            print(f"Foydalanuvchini qo'shish/tekshirishda xatolik (middleware): {e}")

        unsubscribed_channels = await get_unsubscribed_channels(user_id)

        if unsubscribed_channels:
            subscribe_buttons = []
            for i, channel_info in enumerate(unsubscribed_channels):
                channel_name = f"{i + 1}-kanal"
                if channel_info.get('url') and channel_info['url'] != '#':
                    subscribe_buttons.append([InlineKeyboardButton(text=channel_name, url=channel_info['url'])])
                else:
                    subscribe_buttons.append([InlineKeyboardButton(text=channel_name,
                                                                   callback_data=f"check_channel_{channel_info['chat_id']}")])

            subscribe_buttons.append([InlineKeyboardButton(text="Obuna bo'ldim ✅", callback_data="subscribe_true")])

            await message.answer(
                "⚠️ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=subscribe_buttons)
            )
            return

        return await handler(event, data)
