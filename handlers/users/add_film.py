#handlers/users/add_film.py
from aiogram.types import CallbackQuery

from filters import IsBotAdmin
from keyboards.default.buttons import admin_button
from keyboards.inline.buttons import yes_no_button, send_to_channel_button
from loader import dp, db
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from states.film_add_states import FilmAddStates
from aiogram.types import ReplyKeyboardRemove


# handlers/users/add_film.py - YANGILANGAN

@dp.message(F.text == "➕ Kino joylash", IsBotAdmin())
async def film_name_add(message: types.Message, state: FSMContext):
    await message.answer("Filmni kodini yuboring!")
    await state.set_state(FilmAddStates.kod)


@dp.message(F.text, FilmAddStates.kod)
async def film_check_code(message: types.Message, state: FSMContext):
    kod = message.text
    if db.check_code_exists(kod):
        await message.answer("Bu kod allaqachon mavjud. Iltimos, boshqa kod kiriting!")
    elif db.check_code_exists_serial(kod):
        await message.answer("Bu kod serial nomi sifatida allaqachon mavjud. Iltimos, boshqa kod kiriting!")
    else:
        await state.update_data({'kod': kod})
        await message.answer("Film nomi:")
        await state.set_state(FilmAddStates.film_name)


@dp.message(FilmAddStates.film_name)
async def get_name(message: types.Message, state: FSMContext):
    name = message.text
    await state.update_data({'name': name})
    await message.answer("Film banneri uchun rasm jo'nating!")
    await state.set_state(FilmAddStates.film_banner)


# YANGI - Film banneri
@dp.message(FilmAddStates.film_banner, F.photo)
async def get_film_banner(message: types.Message, state: FSMContext):
    try:
        photo = message.photo[-1]
        file_id = photo.file_id
        await state.update_data({'film_banner': file_id})
        await message.answer("Filmni yuboring:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(FilmAddStates.film_id)
    except Exception as e:
        await message.answer("Rasmni yuklashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        print(f"Banner yuklashda xatolik: {e}")


@dp.message(FilmAddStates.film_id, F.video)
async def get_video_file_id(message: types.Message, state: FSMContext):
    film_id = message.video.file_id
    await state.update_data({'film_id': film_id})

    data = await state.get_data()
    text = (
        f"⌨️ KOD: #{data['kod']}\n"
        f"{data['name']}\n\n"
    )

    await message.answer("Barcha ma'lumotlar to'g'rimi?")
    await message.answer_photo(data['film_banner'], caption=text, parse_mode="HTML")
    await message.answer("Tasdiqlaysizmi?", reply_markup=await yes_no_button())

    await state.set_state(FilmAddStates.chekk)


@dp.callback_query(F.data == 'yes', FilmAddStates.chekk)
async def get_check_1(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    all_data = 1

    # Bazaga saqlash (banner bilan)
    db.add_film_data(
        data['name'],
        data['film_id'],
        data['kod'],
        all_data,
        data.get('film_banner', '')
    )

    await call.message.answer("✅ Film bazaga saqlandi!")

    await state.update_data(film_kod=data['kod'])

    # Kanalga yuborish tugmasini ko'rsatish
    await call.message.answer(
        "Filmni kanal yoki guruhga joylamoqchimisiz?",
        reply_markup=await send_to_channel_button(data['kod'])
    )

    await call.message.delete()


@dp.callback_query(F.data == 'no', FilmAddStates.chekk)
async def get_check_0(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Kiritilgan ma'lumotlar o'chirib tashlandi!", reply_markup=admin_button())
    await call.message.delete()
    await state.clear()
