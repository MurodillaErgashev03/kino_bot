from datetime import datetime

from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatJoinRequest

from keyboards.inline.buttons import generate_episode_buttons
from handlers.users import user_router
from loader import db, bot, is_admin


async def get_unsubscribed_channels(user_id: int) -> list:
    if await is_admin(user_id):
        return []

    channels_to_subscribe = []
    all_items = db.get_all_channels()

    if not all_items:
        return []

    user = db.get_user(user_id)
    user_subscription_level = user.get('subscription_level', 'none') if user else 'none'
    last_check_time = user.get('last_check_time') if user else None

    if user_subscription_level == 'none':
        items_to_check = [item for item in all_items if item.get('level', 'primary') == 'primary']
        target_level = 'primary'

    elif user_subscription_level == 'primary':
        if last_check_time:
            if isinstance(last_check_time, str):
                try:
                    last_check_time = datetime.strptime(last_check_time, '%Y-%m-%d %H:%M:%S')
                except:
                    last_check_time = None

            if last_check_time:
                time_passed = datetime.now() - last_check_time
                hours_passed = time_passed.total_seconds() / 3600

                if hours_passed >= 1:
                    items_to_check = [item for item in all_items if item.get('level', 'primary') == 'secondary']
                    target_level = 'secondary'
                else:
                    return []
            else:
                items_to_check = [item for item in all_items if item.get('level', 'primary') == 'secondary']
                target_level = 'secondary'
        else:
            items_to_check = [item for item in all_items if item.get('level', 'primary') == 'secondary']
            target_level = 'secondary'

    else:
        return []

    telegram_items = [item for item in items_to_check if item.get('type', 'channel') in ['channel', 'group']]
    instagram_items = [item for item in items_to_check if item.get('type', 'channel') == 'instagram']

    all_telegram_subscribed = True

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

    if not all_telegram_subscribed:
        for insta in instagram_items:
            channels_to_subscribe.append({
                'chat_id': insta['chat_id'],
                'url': insta['url'],
                'type': 'instagram'
            })

    if all_telegram_subscribed and len(telegram_items) > 0:
        db.update_user_subscription_level(user_id, target_level)

    return channels_to_subscribe


def _build_subscribe_buttons(unsubscribed_channels: list) -> InlineKeyboardMarkup:
    subscribe_buttons = []
    channel_counter = 1

    for item in unsubscribed_channels:
        item_type = item.get('type', 'channel')

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
    return InlineKeyboardMarkup(inline_keyboard=subscribe_buttons)


def _welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔎 Kodlarni qidirish", url="https://t.me/darkvayb")
    ]])


WELCOME_MSG = """👋 Salom

Marhamat, kerakli kodni yuboring:"""


@user_router.message(CommandStart())
async def start_bot(message):
    user_id = message.from_user.id

    # Deep link
    args = message.text.split()
    if len(args) > 1:
        if args[1].startswith('film_'):
            film_kod = args[1].replace('film_', '')
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

        elif args[1].startswith('serial_'):
            serial_kod = args[1].replace('serial_', '')
            serial = db.get_serial_by_name(serial_kod)

            if serial:
                episodes = db.get_episodes_by_serial_id(serial['id'])
                if episodes:
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

    try:
        user = db.get_user(user_id=user_id)
        if not user:
            db.add_user(user_id=str(message.from_user.id), ban=0, sana=str(datetime.now()), status="1")
    except Exception as e:
        print(f"Foydalanuvchini qo'shishda xatolik: {e}")

    unsubscribed_channels = await get_unsubscribed_channels(user_id)

    if not unsubscribed_channels:
        await message.reply(WELCOME_MSG, reply_markup=_welcome_keyboard())
    else:
        await message.answer(
            "⚠️ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling:",
            reply_markup=_build_subscribe_buttons(unsubscribed_channels)
        )


@user_router.callback_query(lambda c: c.data == "subscribe_true")
async def check_subscription(call):
    await call.message.delete()

    user_id = call.from_user.id
    unsubscribed_channels = await get_unsubscribed_channels(user_id)

    if not unsubscribed_channels:
        await call.message.answer(WELCOME_MSG, reply_markup=_welcome_keyboard())
    else:
        await call.message.answer(
            "⚠️ Quyidagi kanallarga obuna bo'ling:",
            reply_markup=_build_subscribe_buttons(unsubscribed_channels)
        )
    await call.answer()


@user_router.chat_join_request()
async def process_join_request(join_request: ChatJoinRequest):
    user_id = join_request.from_user.id
    channel_id = join_request.chat.id
    db.add_join_request(user_id, channel_id)


@user_router.callback_query(lambda c: c.data.startswith("check_channel_"))
async def check_single_channel_subscription(call):
    user_id = call.from_user.id
    unsubscribed_channels = await get_unsubscribed_channels(user_id)

    if not unsubscribed_channels:
        await call.message.answer(WELCOME_MSG, reply_markup=_welcome_keyboard())
        await call.message.delete()
    else:
        await call.message.edit_text(
            "⚠️ Quyidagi kanallarga obuna bo'ling",
            reply_markup=_build_subscribe_buttons(unsubscribed_channels)
        )
    await call.answer()
