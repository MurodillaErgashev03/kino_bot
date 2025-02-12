from aiogram import F, types
from aiogram.fsm.context import FSMContext

import data
from filters import IsBotAdmin
from keyboards.default.buttons import admin_button
from loader import dp, db
from states.film_add_states import FilmAddStates


@dp.message(F.text == "🔝 Asosiy admin panelga qaytish", IsBotAdmin())
async def orqaga(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔝 Asosiy Menyu", reply_markup=admin_button())


@dp.message(F.text == "➖ Kino o'chrish", IsBotAdmin())
async def film_name_add(message: types.Message, state: FSMContext):
    await message.answer("Filmni kodini yuboring !")
    await state.set_state(FilmAddStates.kod_2)


@dp.message(FilmAddStates.kod_2)
async def film_check_code(message: types.Message, state: FSMContext):
    kod = message.text
    if db.check_code_exists(kod):
        await message.answer("🗑 Film o'chirdi !")
        db.delete_film_id(kod)
    else:
        await message.answer("Bu kod orqal hech qanday kino topilmadi !")
    await state.clear()
