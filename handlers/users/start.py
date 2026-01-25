#handlers/users/start.py

import json
from datetime import datetime

from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatJoinRequest

from keyboards.inline.buttons import subscription_button
from loader import dp, db, bot, is_admin
from aiogram import types


async def get_unsubscribed_channels(user_id: int) -> list:
    """
    Foydalanuvchi obuna bo'lmagan yoki so'rov yubormagan kanallar ro'yxatini qaytaradi.

    Instagram akkauntlar faqat barcha telegram kanallarga obuna bo'lmaganida ko'rinadi!
    """

    if await is_admin(user_id):
        return []

    channels_to_subscribe = []
    all_items = db.get_all_channels()

    if not all_items:
        return []

    # Telegram kanallar va Instagram akkauntlarni ajratish
    telegram_items = [item for item in all_items if item.get('type', 'channel') in ['channel', 'group']]
    instagram_items = [item for item in all_items if item.get('type', 'channel') == 'instagram']

    all_telegram_subscribed = True  # Barcha telegram kanallarga obuna bo'lganmi?

    print(f"\n{'=' * 50}")
    print(f"DEBUG: get_unsubscribed_channels - User {user_id}")
    print(f"DEBUG: Jami telegram kanallar: {len(telegram_items)}")
    print(f"DEBUG: Jami instagram: {len(instagram_items)}")

    # FAQAT TELEGRAM KANALLARNI TEKSHIRISH
    for item in telegram_items:
        channel_id_str = item['chat_id']
        channel_url = item.get('url', '#')
        channel_type = item.get('type', 'channel')

        print(f"  - Tekshirilmoqda: {channel_id_str} (type: {channel_type})")

        # PRIVATE KANAL/GURUH TEKSHIRUVI
        if channel_id_str.startswith('private_'):
            user = db.get_user(user_id)
            join_requests = user.get('join_requests', {}) if user else {}
            is_satisfied = len(join_requests) > 0

            if is_satisfied:
                print(f"    ✅ Private - Join request tashlagan")
            else:
                channels_to_subscribe.append({
                    'chat_id': channel_id_str,
                    'url': channel_url,
                    'type': channel_type
                })
                all_telegram_subscribed = False
                print(f"    ❌ Private - Join request YO'Q")

            continue

        # ODDIY KANAL/GURUH TEKSHIRUVI
        try:
            channel_id_int = int(channel_id_str)
        except ValueError:
            print(f"Xato: Noto'g'ri ID: {channel_id_str}")
            continue

        is_satisfied = False

        try:
            chat_member = await bot.get_chat_member(chat_id=channel_id_int, user_id=user_id)
            print(f"    Status: {chat_member.status}")

            if chat_member.status in ['member', 'administrator', 'creator']:
                is_satisfied = True
                print(f"    ✅ OBUNA BO'LGAN")
                if db.has_join_request(user_id, channel_id_int):
                    db.remove_join_request(user_id, channel_id_int)
            elif db.has_join_request(user_id, channel_id_int):
                is_satisfied = True
                print(f"    ✅ JOIN REQUEST TASHLAGAN")

        except TelegramBadRequest as e:
            print(f"    TelegramBadRequest: {e}")
            if db.has_join_request(user_id, channel_id_int):
                is_satisfied = True
                print(f"    ✅ JOIN REQUEST TASHLAGAN")
        except Exception as e:
            print(f"    Xato: {e}")
            if db.has_join_request(user_id, channel_id_int):
                is_satisfied = True
                print(f"    ✅ JOIN REQUEST TASHLAGAN")

        if not is_satisfied:
            channels_to_subscribe.append({
                'chat_id': channel_id_str,
                'url': channel_url,
                'type': channel_type
            })
            all_telegram_subscribed = False
            print(f"    ❌ Obuna/Request YO'Q")

    # INSTAGRAM MANTIQ: Faqat telegram kanallarga obuna BO'LMAGAN bo'lsa ko'rsat
    if not all_telegram_subscribed:
        for insta in instagram_items:
            channels_to_subscribe.append({
                'chat_id': insta['chat_id'],
                'url': insta['url'],
                'type': 'instagram'
            })
            print(f"  📸 Instagram qo'shildi: {insta['url']}")
    else:
        print(f"  ✅ Barcha telegram kanallarga obuna - Instagram ko'rsatilmaydi")

    print(f"DEBUG: Jami obuna bo'lmagan: {len(channels_to_subscribe)}")
    print(f"{'=' * 50}\n")

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
            InlineKeyboardButton(text="🔎 Kodlarni qidirish", url="https://t.me/darkvayb")]])
        await message.reply(msg, reply_markup=chanel)
    else:
        subscribe_buttons = []
        channel_counter = 1
        has_private_channels = False

        for item in unsubscribed_channels:
            item_type = item.get('type', 'channel')
            chat_id = item.get('chat_id', '')

            # Private kanal tekshiruvi
            if chat_id.startswith('private_'):
                has_private_channels = True

            if item_type == 'instagram':
                # Instagram uchun alohida tugma
                subscribe_buttons.append([
                    InlineKeyboardButton(text="📸 Instagram akkauntga obuna bo'ling", url=item['url'])
                ])
            else:
                # Telegram kanal/guruh uchun
                channel_name = f"{channel_counter}-kanal"
                if item['url'] != '#':
                    subscribe_buttons.append([InlineKeyboardButton(text=channel_name, url=item['url'])])
                else:
                    subscribe_buttons.append([
                        InlineKeyboardButton(text=channel_name, callback_data=f"check_channel_{item['chat_id']}")
                    ])
                channel_counter += 1

        subscribe_buttons.append([InlineKeyboardButton(text="Obuna bo'ldim ✅", callback_data="subscribe_true")])

        # Xabar matni
        main_text = "⚠️ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling :"


        await message.answer(main_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=subscribe_buttons))


@dp.callback_query(lambda c: c.data == "subscribe_true")
async def oldim(call: types.CallbackQuery):
    await call.message.delete()  # Eski xabarni o'chirish

    user_id = call.from_user.id

    unsubscribed_channels = await get_unsubscribed_channels(user_id)

    if not unsubscribed_channels:
        msg = """👋 Salom 

Marhamat, kerakli kodni yuboring:"""
        chanel = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔎 Kodlarni qidirish", url="https://t.me/darkvayb")]])
        await call.message.answer(msg, reply_markup=chanel)
    else:
        subscribe_buttons = []
        channel_counter = 1
        has_private_channels = False

        for item in unsubscribed_channels:
            item_type = item.get('type', 'channel')
            chat_id = item.get('chat_id', '')

            # Private kanal tekshiruvi
            if chat_id.startswith('private_'):
                has_private_channels = True

            if item_type == 'instagram':
                # Instagram uchun alohida tugma
                subscribe_buttons.append([
                    InlineKeyboardButton(text="📸 Instagram akkauntga obuna bo'ling", url=item['url'])
                ])
            else:
                # Telegram kanal/guruh uchun
                channel_name = f"{channel_counter}-kanal"
                if item['url'] != '#':
                    subscribe_buttons.append([InlineKeyboardButton(text=channel_name, url=item['url'])])
                else:
                    subscribe_buttons.append([
                        InlineKeyboardButton(text=channel_name, callback_data=f"check_channel_{item['chat_id']}")
                    ])
                channel_counter += 1

        subscribe_buttons.append([InlineKeyboardButton(text="Obuna bo'ldim ✅", callback_data="subscribe_true")])

        # Xabar matni
        main_text = "⚠️ Quyidagi kanallarga obuna bo'ling:"


        await call.message.answer(main_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=subscribe_buttons))
    await call.answer()


# MUHIM HANDLER: Foydalanuvchi kanalga qo'shilish so'rovini yuborganida
@dp.chat_join_request()
async def process_join_request(join_request: ChatJoinRequest):
    user_id = join_request.from_user.id
    channel_id = join_request.chat.id

    # Join request ni bazaga yozish
    db.add_join_request(user_id, channel_id)
    print(f"✅ JOIN REQUEST HANDLER:")
    print(f"   User: {user_id}")
    print(f"   Channel: {channel_id}")
    print(f"   Bu user endi botdan foydalana oladi!")

    # XABAR YUBORMAYMIZ - User o'zi "Obuna bo'ldim" ni bosadi


# callback_data orqali kelgan kanallar uchun
@dp.callback_query(lambda c: c.data.startswith("check_channel_"))
async def check_single_channel_subscription(call: types.CallbackQuery):
    channel_id_str = call.data.split("_")[2]
    user_id = call.from_user.id

    unsubscribed_channels = await get_unsubscribed_channels(user_id)

    if not unsubscribed_channels:
        msg = """👋 Salom 

Marhamat, kerakli kodni yuboring:"""
        chanel = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔎 Kodlarni qidirish", url="https://t.me/darkvayb")]])
        await call.message.answer(msg, reply_markup=chanel)
        await call.message.delete()
    else:
        subscribe_buttons = []
        channel_counter = 1
        has_private_channels = False

        for item in unsubscribed_channels:
            item_type = item.get('type', 'channel')
            chat_id = item.get('chat_id', '')

            # Private kanal tekshiruvi
            if chat_id.startswith('private_'):
                has_private_channels = True

            if item_type == 'instagram':
                subscribe_buttons.append([
                    InlineKeyboardButton(text="📸 Instagram akkauntga obuna bo'ling", url=item['url'])
                ])
            else:
                channel_name = f"{channel_counter}-kanal"
                if item['url'] != '#':
                    subscribe_buttons.append([InlineKeyboardButton(text=channel_name, url=item['url'])])
                else:
                    subscribe_buttons.append([
                        InlineKeyboardButton(text=channel_name, callback_data=f"check_channel_{item['chat_id']}")
                    ])
                channel_counter += 1

        subscribe_buttons.append([InlineKeyboardButton(text="Obuna bo'ldim ✅", callback_data="subscribe_true")])

        # Xabar matni
        main_text = "⚠️ Quyidagi kanallarga obuna bo'ling"

        await call.message.edit_text(main_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=subscribe_buttons))
    await call.answer()