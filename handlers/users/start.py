# start.py

import json
from datetime import datetime

from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatJoinRequest

from keyboards.inline.buttons import subscription_button  # Bu sizning inline tugmalar faylingiz
from loader import dp, db, bot, is_admin
from aiogram import types



async def get_unsubscribed_channels(user_id: int) -> list:
    """
    Foydalanuvchi obuna bo'lmagan yoki so'rov yubormagan kanallar ro'yxatini qaytaradi.
    Har bir element {chat_id: ..., url: ...} lug'ati bo'ladi.
    """

    if await is_admin(user_id):
        return []  # Admin bo'lsa, hech qanday obuna talabi yo'q

    channels_to_subscribe = []
    all_channels = db.get_all_channels()  # Barcha majburiy kanallarni bazadan olamiz

    if not all_channels:
        return []  # Agar majburiy kanallar yo'q bo'lsa

    for channel in all_channels:
        channel_id_str = channel['chat_id']
        channel_url = channel.get('url', '#')  # url ni ham olamiz

        # chat_id ni int ga o'tkazish, bot.get_chat_member talab qiladi
        try:
            channel_id_int = int(channel_id_str)
        except ValueError:
            print(f"Xato: Noto'g'ri kanal ID formati: {channel_id_str}")
            continue  # Noto'g'ri ID bo'lsa, keyingi kanalga o'tamiz

        is_satisfied = False

        try:
            chat_member = await bot.get_chat_member(chat_id=channel_id_int, user_id=user_id)
            print(f"DEBUG: User {user_id}, Channel {channel_id_str}, Status: {chat_member.status}")  # Debug

            if chat_member.status in ['member', 'administrator', 'creator']:
                is_satisfied = True
                # Agar oldingi so'rov qabul qilingan bo'lsa, uni bazadan o'chiramiz
                if db.has_join_request(user_id, channel_id_int):
                    db.remove_join_request(user_id, channel_id_int)
            elif db.has_join_request(user_id, channel_id_int):
                is_satisfied = True  # Foydalanuvchi so'rov yuborgan, talab bajarilgan deb hisoblaymiz

        except TelegramBadRequest as e:
            # Agar bot foydalanuvchini kanalda topa olmasa (masalan, hali so'rov yubormagan yoki bloklagan)
            print(f"DEBUG: TelegramBadRequest for User {user_id}, Channel {channel_id_str}: {e}")  # Debug
            if db.has_join_request(user_id, channel_id_int):
                is_satisfied = True  # Agar so'rov yuborgan bo'lsa, ruxsat beramiz
        except Exception as e:
            print(f"DEBUG: Boshqa xato yuz berdi User {user_id}, Kanal {channel_id_str}: {e}")  # Debug
            is_satisfied = False  # Noma'lum xato bo'lsa, obuna bo'lmagan deb hisoblaymiz

        if not is_satisfied:
            channels_to_subscribe.append({'chat_id': channel_id_str, 'url': channel_url})
            print(f"DEBUG: {channel_id_str} kanaliga obuna bo'lishi kerak. Ro'yxatga qo'shildi.")  # Debug

    return channels_to_subscribe


@dp.message(CommandStart())
async def start_bot(message: types.Message):
    user_id = message.from_user.id
    try:
        user = db.get_user(user_id=user_id)
        if not user:
            db.add_user(user_id=str(message.from_user.id), ban=0, sana=str(datetime.now()), status="1")
            print(f"Yangi foydalanuvchi qo'shildi: {user_id}")
        else:
            print(f"Foydalanuvchi allaqachon mavjud: {user}")
    except Exception as e:
        print(f"Foydalanuvchini qo'shishda xatolik: {e}")

    unsubscribed_channels = await get_unsubscribed_channels(user_id)

    if not unsubscribed_channels:
        msg = """👋 Salom 

Marhamat, kerakli kodni yuboring:"""
        chanel = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔎 Kodlarni qidirish", url="https://t.me/kinomzal")]])
        await message.reply(msg, reply_markup=chanel)
    else:
        subscribe_buttons = []
        for i, channel_info in enumerate(unsubscribed_channels):
            channel_name = f"{i + 1}-kanal"
            if channel_info['url'] != '#':
                subscribe_buttons.append([InlineKeyboardButton(text=channel_name, url=channel_info['url'])])
            else:
                subscribe_buttons.append(
                    [InlineKeyboardButton(text=channel_name, callback_data=f"check_channel_{channel_info['chat_id']}")])

        subscribe_buttons.append([InlineKeyboardButton(text="Obuna bo'ldim ✅", callback_data="subscribe_true")])

        await message.answer(
            "⚠️ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling (agar maxfiy kanal bo'lsa, qo'shilish so'rovini yuboring):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=subscribe_buttons)
        )


@dp.callback_query(lambda c: c.data == "subscribe_true")
async def oldim(call: types.CallbackQuery):
    await call.message.delete()  # Eski xabarni o'chirish

    user_id = call.from_user.id

    # get_unsubscribed_channels funksiyasi chaqiriladi
    # Bu funksiya foydalanuvchining obuna holatini qayta tekshiradi
    # va obuna bo'lmagan yoki so'rov yubormagan kanallar ro'yxatini qaytaradi.
    unsubscribed_channels = await get_unsubscribed_channels(user_id)

    if not unsubscribed_channels:
        # Agar ro'yxat bo'sh bo'lsa, demak foydalanuvchi barcha kanallarga
        # obuna bo'lgan yoki maxfiy kanalga so'rov yuborgan.
        msg = """👋 Salom 

        Marhamat, kerakli kodni yuboring:"""
        chanel = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔎 Kodlarni qidirish", url="https://t.me/kinomzal")]])
        await call.message.answer(msg, reply_markup=chanel)
    else:
        # Agar hali ham obuna bo'lishi kerak bo'lgan kanallar bo'lsa,
        # ularni qaytadan ko'rsatamiz.
        subscribe_buttons = []
        for i, channel_info in enumerate(unsubscribed_channels):
            channel_name = f"{i + 1}-kanal"
            if channel_info['url'] != '#':
                subscribe_buttons.append([InlineKeyboardButton(text=channel_name, url=channel_info['url'])])
            else:
                subscribe_buttons.append(
                    [InlineKeyboardButton(text=channel_name, callback_data=f"check_channel_{channel_info['chat_id']}")])

        subscribe_buttons.append([InlineKeyboardButton(text="Obuna bo'ldim ✅", callback_data="subscribe_true")])

        await call.message.answer(
            "Iltimios! ⚠️ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling (agar maxfiy kanal bo'lsa, qo'shilish so'rovini yuboring):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=subscribe_buttons)
        )
    await call.answer()  # Callback query ni yopish

# Yangi handler: Foydalanuvchi kanalga qo'shilish so'rovini yuborganida
@dp.chat_join_request()
async def process_join_request(join_request: ChatJoinRequest):
    user_id = join_request.from_user.id
    channel_id = join_request.chat.id

    db.add_join_request(user_id, channel_id)
    print(f"Foydalanuvchi {user_id} kanal {channel_id} ga qo'shilish so'rovini yubordi. Bazaga yozildi.")

    # So'rov yuborilgandan keyin foydalanuvchiga yana bir bor tekshirishni taklif qilish mumkin
    # Masalan, uni /start ga yo'naltirish yoki "Obuna bo'ldim" tugmasini qayta bosishni so'rash
    # Hozircha hech narsa yubormaymiz, chunki foydalanuvchi o'zi /start yoki "Obuna bo'ldim" ni bosadi


# callback_data orqali kelgan kanallar uchun, agar URL bo'lmasa (masalan, shaxsiy kanallar uchun)
@dp.callback_query(lambda c: c.data.startswith("check_channel_"))
async def check_single_channel_subscription(call: types.CallbackQuery):
    channel_id_str = call.data.split("_")[2]
    user_id = call.from_user.id

    unsubscribed_channels = await get_unsubscribed_channels(user_id)

    if not unsubscribed_channels:
        msg = """👋 Salom 

        Marhamat, kerakli kodni yuboring:"""
        chanel = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔎 Kodlarni qidirish", url="https://t.me/kinomzal")]])
        await call.message.answer(msg, reply_markup=chanel)
        await call.message.delete()  # Eski xabarni o'chirish
    else:
        # Hali ham obuna bo'lishi kerak bo'lgan kanallar bo'lsa, qayta ko'rsatamiz
        subscribe_buttons = []
        for i, channel_info in enumerate(unsubscribed_channels):
            channel_name = f"{i + 1}-kanal"
            if channel_info['url'] != '#':
                subscribe_buttons.append([InlineKeyboardButton(text=channel_name, url=channel_info['url'])])
            else:
                subscribe_buttons.append(
                    [InlineKeyboardButton(text=channel_name, callback_data=f"check_channel_{channel_info['chat_id']}")])

        subscribe_buttons.append([InlineKeyboardButton(text="Obuna bo'ldim ✅", callback_data="subscribe_true")])

        await call.message.edit_text(
            "Iltimos! ⚠️ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling (agar maxfiy kanal bo'lsa, qo'shilish so'rovini yuboring):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=subscribe_buttons)
        )
    await call.answer()  # Callback query ni yopish