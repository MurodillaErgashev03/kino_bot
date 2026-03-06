import asyncio
from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from filters.admin_bot import IsBotAdmin
from keyboards.default.buttons import admin_button
from handlers.admin import admin_router
from loader import db, bot
from states.states import AdStates


# --- Reklama davomiyligi tugmalari ---

def ad_duration_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏱ 5 daqiqa",   callback_data="ad_dur_5m"),
                InlineKeyboardButton(text="⏱ 15 daqiqa",  callback_data="ad_dur_15m"),
            ],
            [
                InlineKeyboardButton(text="⏱ 30 daqiqa",  callback_data="ad_dur_30m"),
                InlineKeyboardButton(text="⏱ 45 daqiqa",  callback_data="ad_dur_45m"),
            ],
            [
                InlineKeyboardButton(text="🕐 1 soat",     callback_data="ad_dur_1h"),
                InlineKeyboardButton(text="✏️ Qo'lda soat kiritish", callback_data="ad_dur_custom"),
            ],
            [
                InlineKeyboardButton(text="♾ Cheksiz",    callback_data="ad_dur_forever"),
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="ad_dur_cancel"),
            ],
        ]
    )
    return keyboard


DURATION_MAP = {
    "ad_dur_5m":      5  * 60,
    "ad_dur_15m":     15 * 60,
    "ad_dur_30m":     30 * 60,
    "ad_dur_45m":     45 * 60,
    "ad_dur_1h":      1  * 3600,
    "ad_dur_forever": None,
}

DURATION_LABELS = {
    "ad_dur_5m":      "5 daqiqa",
    "ad_dur_15m":     "15 daqiqa",
    "ad_dur_30m":     "30 daqiqa",
    "ad_dur_45m":     "45 daqiqa",
    "ad_dur_1h":      "1 soat",
    "ad_dur_forever": "Cheksiz",
}


# --- 1-qadam: Content yuborish ---

@admin_router.message(F.text == "📤 Reklama yuborish", IsBotAdmin())
async def reklama_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📤 Reklama yuborish uchun rasm, video yoki matn yuboring.\n\n"
        "Bekor qilish uchun /done bosing!",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AdStates.ask_ad_content)


# --- 2-qadam: Content qabul qilish ---

@admin_router.message(AdStates.ask_ad_content)
async def ask_ad_duration(message: types.Message, state: FSMContext):
    if message.text == "/done":
        await state.clear()
        await message.answer("🔝 Asosiy sahifa", reply_markup=admin_button())
        return

    await state.update_data(ad_message_id=message.message_id, ad_chat_id=message.chat.id)

    await message.answer(
        "⏳ Reklama qancha vaqt ko'rinib tursin?\n\n"
        "Tanlangan vaqt o'tgach, reklama barcha foydalanuvchilardan <b>avtomatik o'chiriladi</b>.",
        reply_markup=ad_duration_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdStates.ask_ad_duration)


# --- 3a: Qo'lda soat kiritish ---

@admin_router.callback_query(AdStates.ask_ad_duration, lambda c: c.data == "ad_dur_custom")
async def ask_custom_duration(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "✏️ Necha soat ko'rinib tursin? Faqat raqam kiriting.\n"
        "<i>Masalan: 2  →  2 soat | 0.5  →  30 daqiqa | 1.5  →  1 soat 30 daqiqa</i>",
        parse_mode="HTML"
    )
    await state.set_state(AdStates.ask_ad_custom_hours)
    await call.answer()


# --- 3b: Qo'lda kiritilgan soat ---

@admin_router.message(AdStates.ask_ad_custom_hours)
async def receive_custom_hours(message: types.Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        hours = float(text)
        if hours <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Noto'g'ri format. Faqat musbat raqam kiriting (masalan: 2 yoki 1.5):")
        return

    seconds = int(hours * 3600)
    total_min = int(hours * 60)
    h, m = divmod(total_min, 60)
    if m == 0:
        label = f"{h} soat"
    elif h == 0:
        label = f"{m} daqiqa"
    else:
        label = f"{h} soat {m} daqiqa"

    data = await state.get_data()
    src_message_id = data.get("ad_message_id")
    src_chat_id    = data.get("ad_chat_id")
    await state.clear()

    status_msg = await message.answer(f"⏳ Reklama yuborilmoqda... ({label})")
    await _do_send_ad(message, status_msg, src_chat_id, src_message_id, seconds, label)


# --- 3c: Tayyor tugmadan davomiylik ---

@admin_router.callback_query(AdStates.ask_ad_duration, lambda c: c.data.startswith("ad_dur_"))
async def send_ad_to_users(call: types.CallbackQuery, state: FSMContext):
    chosen = call.data

    if chosen == "ad_dur_cancel":
        await state.clear()
        await call.message.edit_text("❌ Reklama bekor qilindi.")
        await call.message.answer("🔝 Asosiy sahifa", reply_markup=admin_button())
        await call.answer()
        return

    duration_seconds = DURATION_MAP.get(chosen)
    duration_label   = DURATION_LABELS.get(chosen, "?")

    data = await state.get_data()
    src_message_id = data.get("ad_message_id")
    src_chat_id    = data.get("ad_chat_id")

    await state.clear()
    await call.message.edit_text(f"⏳ Reklama yuborilmoqda... ({duration_label})")
    await call.answer()

    await _do_send_ad(call.message, None, src_chat_id, src_message_id, duration_seconds, duration_label)


# --- Reklama yuborish funksiyasi ---

async def _do_send_ad(reply_target, status_msg, src_chat_id: int, src_message_id: int,
                      duration_seconds, duration_label: str):
    users = db.select_all_users()
    sent_messages = []
    count = 0

    for user in users:
        user_id = user['user_id']
        try:
            sent = await bot.copy_message(
                chat_id=user_id,
                from_chat_id=src_chat_id,
                message_id=src_message_id
            )
            sent_messages.append((int(user_id), sent.message_id))
            count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"Reklama yuborishda xato ({user_id}): {e}")

    if duration_seconds is not None:
        delete_after = datetime.now() + timedelta(seconds=duration_seconds)
        result_text = (
            f"✅ Reklama <b>{count}</b> ta foydalanuvchiga yuborildi.\n"
            f"⏱ Davomiyligi: <b>{duration_label}</b>\n"
            f"🗑 O'chirilish vaqti: <b>{delete_after.strftime('%H:%M:%S')}</b>"
        )
    else:
        result_text = (
            f"✅ Reklama <b>{count}</b> ta foydalanuvchiga yuborildi.\n"
            f"♾ Davomiyligi: <b>Cheksiz</b> (o'chirilmaydi)"
        )

    await reply_target.answer(result_text, reply_markup=admin_button(), parse_mode="HTML")

    if duration_seconds is not None and sent_messages:
        asyncio.create_task(_delete_ads_after(sent_messages, duration_seconds))


async def _delete_ads_after(sent_messages: list[tuple], delay_seconds: int):
    await asyncio.sleep(delay_seconds)

    for chat_id, message_id in sent_messages:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"Reklamani o'chirishda xato ({chat_id}): {e}")

    print(f"✅ {len(sent_messages)} ta reklama xabari o'chirildi.")
