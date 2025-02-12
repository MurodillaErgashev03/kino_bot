import time
from typing import Any, Awaitable, Callable, cast, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from handlers.users.start import is_user_subscribed
from keyboards.inline.buttons import subscription_button


class UserCheckMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],  # Tiplash to'g'rilandi
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        event = cast(Update, event)
        if event.message:
            user = event.message.from_user
            user_id = user.id

            # Kanallarga obuna bo'lganini tekshirish
            if not await is_user_subscribed(user_id):
                # Agar foydalanuvchi obuna bo'lmagan bo'lsa, kanallarning URL'larini yuborish
                await event.message.answer(
                    "⚠️ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling:",
                    reply_markup=await subscription_button()
                )
                return  # Agar obuna bo'lmagan bo'lsa, to'xtatamiz

        return await handler(event, data)