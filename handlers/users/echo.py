from datetime import datetime

from aiogram import F, types
from aiogram.fsm.context import FSMContext

from keyboards.inline.buttons import generate_episode_buttons
from handlers.users import user_router
from loader import db


@user_router.message(F.text)
async def return_film_or_serial(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    user_id = message.from_user.id

    try:
        user = db.get_user(user_id=user_id)
        if not user:
            db.add_user(user_id=message.from_user.id, ban=0, sana=str(datetime.now()), status="1")
    except Exception as e:
        print(f"Foydalanuvchini qo'shishda xatolik: {e}")

    # Kinoni qidirish
    film = db.get_film_by_name(user_input)

    if film:
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
        return

    # Serialni qidirish
    serial = db.get_serial_by_name(user_input)

    if serial:
        episodes = db.get_episodes_by_serial_id(serial['id'])
        if episodes:
            await state.update_data(serial_id=serial['id'])
            await message.answer_photo(
                serial['serial_banner'],
                caption=serial['serial_title'],
                reply_markup=generate_episode_buttons(episodes, serial_id=serial['id'])
            )
        else:
            await message.answer(f"Bu serialda hozircha qismlar mavjud emas !")
        return

    await message.answer(f"{user_input} - id bilan hech qanday kino yoki serial topilmadi ❌")
