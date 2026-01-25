#handlers/users/start.py

import json
from datetime import datetime

from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatJoinRequest

from keyboards.inline.buttons import subscription_button, generate_episode_buttons
from loader import dp, db, bot, is_admin
from aiogram import types


async def get_unsubscribed_channels(user_id: int) -> list:
    """
    User uchun obuna bo'lishi kerak bo'lgan kanallarni qaytaradi.

    Mantiq:
    1. Yangi user -> faqat PRIMARY kanallar
    2. PRIMARY tugallagan -> 1-2 soat kutadi
    3. 1-2 soat o'tgandan keyin -> SECONDARY kanallar
    """

    if await is_admin(user_id):
        return []

    channels_to_subscribe = []
    all_items = db.get_all_channels()

    if not all_items:
        return []

    # User ma'lumotlarini olish
    user = db.get_user(user_id)
    user_subscription_level = user.get('subscription_level', 'none') if user else 'none'
    last_check_time = user.get('last_check_time') if user else None

    print(f"\n{'=' * 50}")
    print(f"DEBUG: User {user_id}")
    print(f"  - Subscription level: {user_subscription_level}")
    print(f"  - Last check time: {last_check_time}")

    # LEVEL bo'yicha filtrlash
    if user_subscription_level == 'none':
        # Yangi user - faqat PRIMARY kanallar
        items_to_check = [item for item in all_items if item.get('level', 'primary') == 'primary']
        target_level = 'primary'
        print(f"  - Yangi user -> PRIMARY kanallar ({len(items_to_check)} ta)")

    elif user_subscription_level == 'primary':
        # PRIMARY tugallangan - vaqtni tekshirish
        if last_check_time:
            # String ni datetime ga aylantirish
            if isinstance(last_check_time, str):
                try:
                    last_check_time = datetime.strptime(last_check_time, '%Y-%m-%d %H:%M:%S')
                except:
                    last_check_time = None

            if last_check_time:
                # 1-2 soat o'tganini tekshirish (1 soat = 3600 sekund)
                time_passed = datetime.now() - last_check_time
                hours_passed = time_passed.total_seconds() / 3600

                print(f"  - PRIMARY tugallangan: {hours_passed:.2f} soat oldin")

                if hours_passed >= 1:  # 1 soat o'tgan
                    # SECONDARY kanallarni ko'rsatish
                    items_to_check = [item for item in all_items if item.get('level', 'primary') == 'secondary']
                    target_level = 'secondary'
                    print(f"  - 1 soat o'tgan -> SECONDARY kanallar ({len(items_to_check)} ta)")
                else:
                    # Hali vaqt yo'q
                    print(f"  - Hali {1 - hours_passed:.2f} soat kutish kerak")
                    return []
            else:
                # Vaqt noma'lum - SECONDARY ni ko'rsatish
                items_to_check = [item for item in all_items if item.get('level', 'primary') == 'secondary']
                target_level = 'secondary'
        else:
            # Vaqt yo'q - SECONDARY ni ko'rsatish
            items_to_check = [item for item in all_items if item.get('level', 'primary') == 'secondary']
            target_level = 'secondary'

    else:
        # Hammasi tugallangan
        print(f"  - Barcha darajalar tugallangan")
        return []

    # Telegram va Instagram ajratish
    telegram_items = [item for item in items_to_check if item.get('type', 'channel') in ['channel', 'group']]
    instagram_items = [item for item in items_to_check if item.get('type', 'channel') == 'instagram']

    all_telegram_subscribed = True

    # Telegram kanallarni tekshirish
    for item in telegram_items:
        channel_id_str = item['chat_id']
        channel_url = item.get('url', '#')
        channel_type = item.get('type', 'channel')

        try:
            channel_id_int = int(channel_id_str)
        except ValueError:
            continue

        is_satisfied = False

        try:
            chat_member = await bot.get_chat_member(chat_id=channel_id_int, user_id=user_id)

            if chat_member.status in ['member', 'administrator', 'creator']:
                is_satisfied = True
                if db.has_join_request(user_id, channel_id_int):
                    db.remove_join_request(user_id, channel_id_int)

            elif db.has_join_request(user_id, channel_id_int):
                is_satisfied = True

        except TelegramBadRequest:
            if db.has_join_request(user_id, channel_id_int):
                is_satisfied = True
        except Exception:
            if db.has_join_request(user_id, channel_id_int):
                is_satisfied = True

        if not is_satisfied:
            channels_to_subscribe.append({
                'chat_id': channel_id_str,
                'url': channel_url,
                'type': channel_type
            })
            all_telegram_subscribed = False

    # Instagram mantiq
    if not all_telegram_subscribed:
        for insta in instagram_items:
            channels_to_subscribe.append({
                'chat_id': insta['chat_id'],
                'url': insta['url'],
                'type': 'instagram'
            })

    # Agar barcha telegram kanallarga obuna bo'lgan bo'lsa, user level ni yangilash
    if all_telegram_subscribed and len(telegram_items) > 0:
        db.update_user_subscription_level(user_id, target_level)
        print(f"DEBUG: ✅ User level yangilandi: {target_level}")

    print(f"DEBUG: Obuna bo'lishi kerak: {len(channels_to_subscribe)} ta")
    print(f"{'=' * 50}\n")

    return channels_to_subscribe



@dp.message(CommandStart())
async def start_bot(message: types.Message):
    user_id = message.from_user.id

    # Deep link tekshirish
    args = message.text.split()
    if len(args) > 1:
        # FILM uchun
        if args[1].startswith('film_'):
            film_kod = args[1].replace('film_', '')

            # Filmni bazadan olish
            film = db.get_film_by_name(film_kod)

            if film:
                caption = (
                    f"⌨️ KOD: #{film_kod}\n"
                    f"{film['file_name']}\n\n"
                    f"📌 @darkvayb"
                )
                await message.answer_video(film['file_id'], caption=caption, parse_mode="HTML")
                return
            else:
                await message.answer("❌ Film topilmadi!")
                return

        # SERIAL uchun
        elif args[1].startswith('serial_'):
            serial_kod = args[1].replace('serial_', '')

            # Serialni bazadan olish
            serial = db.get_serial_by_name(serial_kod)

            if serial:
                episodes = db.get_episodes_by_serial_id(serial['id'])

                if episodes:
                    # Epizodlar tugmalarini ko'rsatish
                    await message.answer_photo(
                        serial['serial_banner'],
                        caption=serial['serial_title'],
                        reply_markup=generate_episode_buttons(episodes, serial_id=serial['id'])
                    )
                    return
                else:
                    await message.answer("❌ Bu serialda hozircha qismlar mavjud emas!")
                    return
            else:
                await message.answer("❌ Serial topilmadi!")
                return

    # Oddiy /start - obuna tekshirish
    try:
        user = db.get_user(user_id=user_id)
        if not user:
            db.add_user(user_id=str(message.from_user.id), ban=0, sana=str(datetime.now()), status="1")
            print(f"Yangi foydalanuvchi qo'shildi: {user_id}")
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
        # Obuna kerak
        subscribe_buttons = []
        channel_counter = 1

        for item in unsubscribed_channels:
            item_type = item.get('type', 'channel')
            chat_id = item.get('chat_id', '')

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

        main_text = "⚠️ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling:"
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