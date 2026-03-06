from aiogram.types import CallbackQuery

from filters import IsBotAdmin
from keyboards.default.buttons import admin_button
from keyboards.inline.buttons import yes_no_button, send_to_channel_button
from handlers.admin import admin_router
from loader import db
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from states.states import FilmStates


@admin_router.message(F.text == "➕ Kino joylash", IsBotAdmin())
async def film_name_add(message: types.Message, state: FSMContext):
    await message.answer("Filmni kodini yuboring!")
    await state.set_state(FilmStates.kod)


@admin_router.message(F.text, FilmStates.kod)
async def film_check_code(message: types.Message, state: FSMContext):
    kod = message.text
    if db.check_code_exists(kod):
        await message.answer("Bu kod allaqachon mavjud. Iltimos, boshqa kod kiriting!")
    elif db.check_code_exists_serial(kod):
        await message.answer("Bu kod serial nomi sifatida allaqachon mavjud. Iltimos, boshqa kod kiriting!")
    else:
        await state.update_data({'kod': kod})
        await message.answer("Film nomi:")
        await state.set_state(FilmStates.film_name)


@admin_router.message(FilmStates.film_name)
async def get_name(message: types.Message, state: FSMContext):
    name = message.text
    await state.update_data({'name': name})
    await message.answer("Film banneri uchun rasm jo'nating!")
    await state.set_state(FilmStates.film_banner)


@admin_router.message(FilmStates.film_banner, F.photo)
async def get_film_banner(message: types.Message, state: FSMContext):
    try:
        photo = message.photo[-1]
        file_id = photo.file_id
        await state.update_data({'film_banner': file_id})
        await message.answer("Filmni yuboring:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(FilmStates.film_id)
    except Exception as e:
        await message.answer("Rasmni yuklashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        print(f"Banner yuklashda xatolik: {e}")


@admin_router.message(FilmStates.film_id, F.video)
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

    await state.set_state(FilmStates.chekk)


@admin_router.callback_query(F.data == 'yes', FilmStates.chekk)
async def get_check_1(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    all_data = 1

    db.add_film_data(
        data['name'],
        data['film_id'],
        data['kod'],
        all_data,
        data.get('film_banner', '')
    )

    await call.message.answer("✅ Film bazaga saqlandi!")

    await state.update_data(film_kod=data['kod'])

    await call.message.answer(
        "Filmni kanal yoki guruhga joylamoqchimisiz?",
        reply_markup=await send_to_channel_button(data['kod'])
    )

    await call.message.delete()


@admin_router.callback_query(F.data == 'no', FilmStates.chekk)
async def get_check_0(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Kiritilgan ma'lumotlar o'chirib tashlandi!", reply_markup=admin_button())
    await call.message.delete()
    await state.clear()


# --- Kino o'chirish ---

@admin_router.message(F.text == "➖ Kino o'chrish", IsBotAdmin())
async def film_delete(message: types.Message, state: FSMContext):
    await message.answer("Filmni kodini yuboring !")
    await state.set_state(FilmStates.kod_delete)


@admin_router.message(FilmStates.kod_delete)
async def film_delete_check(message: types.Message, state: FSMContext):
    kod = message.text
    if db.check_code_exists(kod):
        await message.answer("🗑 Film o'chirdi !")
        db.delete_film_id(kod)
    else:
        await message.answer("Bu kod orqal hech qanday kino topilmadi !")
    await state.clear()
