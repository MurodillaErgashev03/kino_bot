from aiogram import F, types
from aiogram.fsm.context import FSMContext
from keyboards.inline.buttons import generate_episode_buttons
from loader import dp, db

# Echo funksiyasi
async def echo_message(message: types.Message):
    await message.answer(f"{message.text} - id bilan hech qanday kino yoki serial topilmadi ❌")

# Kino yoki serialni qidirish
@dp.message(F.text)
async def return_film_or_serial(message: types.Message, state: FSMContext):
    user_input = message.text.strip()

    # Agar user input raqam bo'lsa, kino id bilan qidiramiz
    if user_input.isdigit():
        film_id = int(user_input)
        row = db.get_film_by_id(film_id)

        if row:
            name_film = db.get_film_by_name(film_id)  # get_film_by_name ga film_id uzatiladi
            text = (
                f"⌨️ KOD: #{row['kod']}\n"
                f"📑 Name: {name_film['file_name']}\n\n"
                f" 📍Bizning bot: @kmfilmlar_bot"
            )
            await message.answer_video(row['file_id'], caption=text, parse_mode="HTML")
        else:
            await echo_message(message)

    # Agar raqam bo'lmasa, serial nomi bilan qidiramiz
    else:
        serial_name = user_input
        serial = db.get_serial_by_name(serial_name)

        if serial:
            episodes = db.get_episodes_by_serial_id(serial['id'])  # Serialga tegishli qismlar
            if episodes:
                # serial_id'ni state ga saqlash
                await state.update_data(serial_id=serial['id'])

                await message.answer_photo(
                    serial['serial_banner'],
                    caption=serial['serial_title'],  # Serial nomi
                    reply_markup=generate_episode_buttons(episodes,serial_id=serial['id'])
                )
            else:
                await message.answer(f"Bu serialda hozircha qismlar mavjud emas.")
        else:
            await echo_message(message)

