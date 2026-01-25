#keyboards/default/buttons.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton


def admin_button():
    button = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📤 Reklama yuborish"), KeyboardButton(text="🛎 Obunachilar soni")],
            [KeyboardButton(text="📀 Kino joylash / O'chrish"), KeyboardButton(text="📌Majburiy Obuna")],
            [KeyboardButton(text="📽 Seril joylash / O'chrish"), KeyboardButton(text="🤵🏻‍♂️ Admin qo'shish / o'chrish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return button


def majburiy_obuna():
    button = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Kanal qo'shish"), KeyboardButton(text="➖ Kanal o'chrish")],
            [KeyboardButton(text="👁‍🗨 Majburiy kanallarni ko'rish"), KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return button


# YANGI FUNKSIYA - Kanal/Guruh/Instagram tanlash
def choose_subscription_type():
    button = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Kanal qo'shish")],
            [KeyboardButton(text="👥 Guruh qo'shish")],
            [KeyboardButton(text="📸 Instagram akkaunt qo'shish")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return button


# YANGI FUNKSIYA - Kanal qo'shish usulini tanlash
def choose_channel_add_method():
    button = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Username orqali qo'shish")],
            [KeyboardButton(text="📨 Kanal habari orqali qo'shish")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return button


def film_delete_or_join():
    button = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Kino joylash"), KeyboardButton(text="➖ Kino o'chrish")],
            [KeyboardButton(text="🔝 Asosiy admin panelga qaytish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return button


def serial_delete_or_join():
    button = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Yangi serial joylash"), KeyboardButton(text="➖ Serial o'chrish")],
            [KeyboardButton(text="➕ Serialning qismlarini qo'shish")],
            [KeyboardButton(text="🔝 Asosiy admin panelga qaytish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return button


def add_admin():
    button = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Admin qo'shish"), KeyboardButton(text="➖ Admin o'chrish")],
            [KeyboardButton(text="👁‍🗨 Adminlarni ko'rish"), KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return button


def confirm_cancel_buttons():
    """
    Tasdiqlash va bekor qilish tugmalari uchun inline klaviatura.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]
        ]
    )
    return keyboard