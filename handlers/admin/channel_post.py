from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from handlers.admin import admin_router
from loader import db, bot
from keyboards.inline.buttons import select_channel_for_post, watch_film_button, watch_serial_button
from states.states import ChannelPostStates


# --- Filmni kanalga yuborish ---

@admin_router.callback_query(lambda c: c.data.startswith('send_film_'))
async def ask_select_channel(callback_query: CallbackQuery, state: FSMContext):
    kod = callback_query.data.split('_')[2]

    film = db.get_film_by_name(kod)
    if not film:
        await callback_query.answer("❌ Film topilmadi!")
        return

    await state.update_data(film_kod=kod)
    await state.set_state(ChannelPostStates.waiting_for_channel_selection)

    await callback_query.message.edit_text(
        "📤 Qaysi kanal yoki guruhga yubormoqchisiz?",
        reply_markup=await select_channel_for_post()
    )
    await callback_query.answer()


# --- Serialni kanalga yuborish ---

@admin_router.callback_query(lambda c: c.data.startswith('send_serial_'))
async def ask_select_channel_for_serial(callback_query: CallbackQuery, state: FSMContext):
    serial_kod = callback_query.data.split('_')[2]

    serial = db.get_serial_by_name(serial_kod)
    if not serial:
        await callback_query.answer("❌ Serial topilmadi!")
        return

    await state.update_data(serial_kod=serial_kod)
    await state.set_state(ChannelPostStates.waiting_for_channel_selection)

    await callback_query.message.edit_text(
        "📤 Qaysi kanal yoki guruhga yubormoqchisiz?",
        reply_markup=await select_channel_for_post()
    )
    await callback_query.answer()


# --- Tanlangan kanalga yuborish ---

@admin_router.callback_query(ChannelPostStates.waiting_for_channel_selection, lambda c: c.data.startswith('post_to_'))
async def post_to_selected_channel(callback_query: CallbackQuery, state: FSMContext):
    chat_id = callback_query.data.replace('post_to_', '')

    data = await state.get_data()
    film_kod = data.get('film_kod')
    serial_kod = data.get('serial_kod')

    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username

        # FILM
        if film_kod:
            film = db.get_film_by_name(film_kod)
            if not film:
                await callback_query.answer("❌ Film topilmadi!")
                return

            film_banner = film.get('film_banner')
            if not film_banner:
                await callback_query.answer("❌ Film banneri topilmadi!")
                return

            caption = (
                f"🎬 {film['file_name']}\n\n"
                f"⌨️ KOD: #{film_kod}\n\n"
                f"📌 @{bot_username}"
            )

            await bot.send_photo(
                chat_id=int(chat_id),
                photo=film_banner,
                caption=caption,
                reply_markup=await watch_film_button(film_kod, bot_username)
            )

            await callback_query.message.edit_text("✅ Film muvaffaqiyatli yuborildi!")
            await callback_query.answer("✅ Yuborildi!")

        # SERIAL
        elif serial_kod:
            serial = db.get_serial_by_name(serial_kod)
            if not serial:
                await callback_query.answer("❌ Serial topilmadi!")
                return

            episodes = db.get_episodes_by_serial_id(serial['id'])
            episodes_count = len(episodes) if episodes else 0

            caption = (
                f"📺 {serial['serial_title']}\n\n"
                f"⌨️ KOD: #{serial_kod}\n"
                f"📊 Qismlar: {episodes_count} ta\n\n"
                f"📌 @{bot_username}"
            )

            await bot.send_photo(
                chat_id=int(chat_id),
                photo=serial['serial_banner'],
                caption=caption,
                reply_markup=await watch_serial_button(serial_kod, bot_username)
            )

            await callback_query.message.edit_text("✅ Serial muvaffaqiyatli yuborildi!")
            await callback_query.answer("✅ Yuborildi!")

        else:
            await callback_query.answer("❌ Xatolik!")
            return

        await state.clear()

    except Exception as e:
        await callback_query.answer(f"❌ Xatolik: {str(e)}")
        await callback_query.message.edit_text(f"❌ Xatolik yuz berdi: {str(e)}")
        await state.clear()


# --- Bekor qilish ---

@admin_router.callback_query(F.data == "cancel_send")
async def cancel_send(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.delete()
    await callback_query.answer("❌ Bekor qilindi")
