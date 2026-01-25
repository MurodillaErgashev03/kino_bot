#headers/users/echo.py
from datetime import datetime

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
    user_id = message.from_user.id

    try:
        user = db.get_user(user_id=user_id)
        if not user:
            db.add_user(user_id=message.from_user.id, ban=0, sana=str(datetime.now()), status="1")
            print(f"Yangi foydalanuvchi qo'shildi: {user_id}")
        else:
            print(f"Foydalanuvchi allaqachon mavjud: {user}")
    except Exception as e:
        print(f"Foydalanuvchini qo'shishda xatolik: {e}")
    # Clean up user input

    # First, try to get the film by name or ID
    film = db.get_film_by_name(user_input)

    if film:
        print(film)  # Check the contents of 'film'
        kod = film.get('kod')
        file_id = film.get('file_id')

        if kod and file_id:
            text = (
                f"⌨️ KOD: #{kod}\n"
                f"{film['file_name']}\n\n"
                f"📌 @darkvayb"
            )
            await message.answer_video(file_id, caption=text, parse_mode="HTML")
        else:
            await message.answer("Filmning video fayli mavjud emas yoki kodni topa olmadik.")
    else:
        # If no film found, search for the serial by name or ID
        serial = db.get_serial_by_name(user_input)

        if serial:
            episodes = db.get_episodes_by_serial_id(serial['id'])  # Get episodes for the serial
            if episodes:
                # Save the serial_id in state
                await state.update_data(serial_id=serial['id'])

                await message.answer_photo(
                    serial['serial_banner'],
                    caption=serial['serial_title'],  # Serial name
                    reply_markup=generate_episode_buttons(episodes, serial_id=serial['id'])
                )
            else:
                await message.answer(f"Bu serialda hozircha qismlar mavjud emas !")
        else:
            await echo_message(message)
