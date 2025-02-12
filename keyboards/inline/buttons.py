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
    channels = db.get_all_channels()  # channels: [{'chat_id': '-1001562032753', 'url': 'https://t.me/...'}, ...]
    inline_keyboard = []

    for sanoq, channel in enumerate(channels, start=1):
        button = InlineKeyboardButton(text=f"{sanoq} - kanal", url=channel['url'])
        inline_keyboard.append([button])

    inline_keyboard.append([
        InlineKeyboardButton(text="Obuna bo'ldim✅", callback_data="subscribe_true")  # callback_data qisqa va aniq
    ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

async def delete_channel_button():
    kanallar = db.get_all_channels()
    inline_keyboard = []

    for kanal in kanallar:
        tugma = InlineKeyboardButton(
            text=f"{kanal['url']}",
            callback_data=f"delete_channel_{kanal['chat_id']}"
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




from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def generate_episode_buttons(episodes, serial_id, page=1, per_page=5):
    buttons = []
    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    # Epizodlarni tugmalarga ajratamiz
    row = []
    for ep in episodes[start_index:end_index]:
        button = InlineKeyboardButton(
            text=f"{ep['episode_number']}",
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
        pagination_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"pagination_{serial_id}_{page - 1}"))
    if end_index < len(episodes):
        pagination_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"pagination_{serial_id}_{page + 1}"))

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
