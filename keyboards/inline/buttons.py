#keyboards/inline/buttons.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from loader import db


async def yes_no_button():
    button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ha", callback_data="yes"),
             InlineKeyboardButton(text="Yo'q", callback_data="no")]]

    )
    return button


async def yes_no_button_episode():
    button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ha", callback_data="yes_episode"),
             InlineKeyboardButton(text="Yo'q", callback_data="no_episode")]]

    )
    return button


async def yes_no_button_confirmation():
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ha", callback_data="confirm_yes"),
             InlineKeyboardButton(text="Yo'q", callback_data="confirm_no")]
        ]
    )
    return buttons


async def yes_no_button_2():
    button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ha", callback_data="yeah"),
             InlineKeyboardButton(text="Yo'q", callback_data="noo")]]

    )
    return button


async def subscription_button():
    channels = db.get_all_channels()  # channels: [{'chat_id': '-1001562032753', 'url': 'https://t.me/...', 'type': 'channel'}, ...]
    inline_keyboard = []

    for sanoq, channel in enumerate(channels, start=1):
        channel_type = channel.get('type', 'channel')

        # Type bo'yicha emoji tanlash
        if channel_type == 'instagram':
            emoji = "📸"
            text = f"{emoji} Instagram"
        elif channel_type == 'group':
            emoji = "👥"
            text = f"{sanoq} - guruh"
        else:  # channel
            emoji = "📢"
            text = f"{sanoq} - kanal"

        button = InlineKeyboardButton(text=text, url=channel['url'])
        inline_keyboard.append([button])

    inline_keyboard.append([
        InlineKeyboardButton(text="Obuna bo'ldim✅", callback_data="subscribe_true")
    ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def delete_channel_button():
    """O'chirish uchun barcha obunalarni ko'rsatish (type bilan)"""
    items = db.get_all_channels()
    inline_keyboard = []

    for item in items:
        item_type = item.get('type', 'channel')
        url = item['url']

        # Type bo'yicha ko'rsatish
        if item_type == 'instagram':
            # Instagram username'ini URL dan ajratib olish
            username = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
            text = f"📸 Instagram: {username}"
        elif item_type == 'group':
            text = f"👥 Guruh: {url}"
        else:  # channel
            text = f"📢 Kanal: {url}"

        tugma = InlineKeyboardButton(
            text=text,
            callback_data=f"delete_channel_{item['chat_id']}"
        )
        inline_keyboard.append([tugma])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def delete_admin_button():
    adminlar = db.get_all_admins()  # Barcha adminlarni olish
    inline_keyboard = []

    for admin in adminlar:
        tugma = InlineKeyboardButton(
            text=f"{admin['user_name']}",  # Adminning user_name'ini ko'rsatish
            callback_data=f"delete_admin_{admin['user_id']}"  # Callback uchun user_id ni ishlatish
        )
        inline_keyboard.append([tugma])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def generate_episode_buttons(episodes, serial_id, page=1, per_page=5):
    buttons = []
    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    # Epizodlarni tugmalarga ajratamiz
    row = []
    for ep in episodes[start_index:end_index]:
        button = InlineKeyboardButton(
            text=f"{ep['episode_number']}-qism ",
            callback_data=f"view_episode_{serial_id}_{ep['episode_number']}"
        )
        row.append(button)

        # Har beshta qismdan keyin qatorni to'ldiramiz
        if len(row) == 5:
            buttons.append(row)
            row = []

    # Agar qoldiq tugma bo'lsa (qator to'liq bo'lmasa)
    if row:
        buttons.append(row)

    # Sahifalash uchun "Oldingi" va "Keyingi" tugmalari
    pagination_row = []
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"pagination_{serial_id}_{page - 1}"))
    if end_index < len(episodes):
        pagination_row.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"pagination_{serial_id}_{page + 1}"))

    if pagination_row:
        buttons.append(pagination_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def add_episode_button():
    seriallar = db.get_serial()
    inline_keyboard = []

    for serial in seriallar:
        tugma = InlineKeyboardButton(
            text=f"{serial['serial_name']}",
            callback_data=f"add_episode_{serial['id']}"  # Callback uchun serial_id ishlatilmoqda
        )
        inline_keyboard.append([tugma])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# keyboards/inline/buttons.py

async def view_channels_paginated(page: int = 1, per_page: int = 10):
    """Kanallarni paginated ko'rsatish"""
    offset = (page - 1) * per_page
    items = db.get_channels_paginated(offset, per_page)
    total = db.count_channels()
    total_pages = (total + per_page - 1) // per_page

    inline_keyboard = []

    for item in items:
        item_type = item.get('type', 'channel')
        level = item.get('level', 'primary')
        url = item['url']

        # Level emoji
        level_emoji = "1️⃣" if level == 'primary' else "2️⃣"

        # Type emoji
        if item_type == 'instagram':
            username = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
            text = f"{level_emoji} 📸 {username}"
        elif item_type == 'group':
            text = f"{level_emoji} 👥 Guruh"
        else:
            text = f"{level_emoji} 📢 Kanal"

        inline_keyboard.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"view_ch_{item['chat_id']}"
            )
        ])

    # Pagination tugmalari
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"ch_page_{page - 1}")
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"ch_page_{page + 1}")
        )

    if nav_buttons:
        inline_keyboard.append(nav_buttons)

    # Sahifa raqami
    inline_keyboard.append([
        InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="ignore")
    ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def channel_detail_buttons(chat_id: str):
    """Kanal tafsilotlari va sozlamalar"""
    channels = db.get_all_channels()
    channel_info = None

    for ch in channels:
        if ch['chat_id'] == chat_id:
            channel_info = ch
            break

    if not channel_info:
        return None

    current_level = channel_info.get('level', 'primary')

    keyboard = []

    # Level o'zgartirish tugmalari
    if current_level == 'primary':
        keyboard.append([
            InlineKeyboardButton(
                text="⬆️ 2-darajali qilish",
                callback_data=f"set_lvl_secondary_{chat_id}"
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                text="⬇️ 1-darajali qilish",
                callback_data=f"set_lvl_primary_{chat_id}"
            )
        ])

    # Orqaga tugma
    keyboard.append([
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_ch_list")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def send_to_channel_button(kod: str):
    """Kanalga yuborish tugmasi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Kanalga yuborish", callback_data=f"send_film_{kod}")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_send")]
        ]
    )
    return keyboard


async def select_channel_for_post():
    """Kanal tanlash uchun tugmalar"""
    channels = db.get_all_channels()
    keyboard = []

    for ch in channels:
        ch_type = ch.get('type', 'channel')
        url = ch.get('url', '')
        chat_id = ch.get('chat_id', '')

        # Faqat telegram kanal va guruhlar
        if ch_type in ['channel', 'group']:
            # Kanal nomini olish
            try:
                name = url.split('/')[-1]
                emoji = "📢" if ch_type == 'channel' else "👥"
                text = f"{emoji} {name}"
            except:
                text = f"Kanal/Guruh"

            keyboard.append([
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"post_to_{chat_id}"
                )
            ])

    keyboard.append([
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_send")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def watch_film_button(kod: str, bot_username: str):
    """Tomosha qilish tugmasi (deep link)"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🔵 Tomosha qilish",
                url=f"https://t.me/{bot_username}?start=film_{kod}"
            )]
        ]
    )
    return keyboard

async def send_to_channel_button_serial(serial_kod: str):
    """Serial uchun kanalga yuborish tugmasi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Kanalga yuborish", callback_data=f"send_serial_{serial_kod}")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_send")]
        ]
    )
    return keyboard

async def watch_serial_button(serial_kod: str, bot_username: str):
    """Serial tomosha qilish tugmasi (deep link)"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🔵 Tomosha qilish",
                url=f"https://t.me/{bot_username}?start=serial_{serial_kod}"
            )]
        ]
    )
    return keyboard