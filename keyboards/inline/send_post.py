from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def refer_post():
    postd = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=" Kanalga joylash ", callback_data='send')],
            [InlineKeyboardButton(text="Chiqindiga tashlash", callback_data='trash')]
        ]

    )
    return postd
