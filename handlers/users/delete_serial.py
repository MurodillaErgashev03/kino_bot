from aiogram import F, types
from aiogram.fsm.context import FSMContext

from loader import dp, db
from states.film_add_states import FilmAddStates


@dp.message(F.text == "➖ Serial o'chrish")
async def ask_for_serial_name_to_delete(message: types.Message, state: FSMContext):
    await message.answer("O'chirmoqchi bo'lgan serialingiz nomini yuboring:")
    await state.set_state(FilmAddStates.waiting_for_serial_delete)


@dp.message(FilmAddStates.waiting_for_serial_delete, F.text)
async def delete_serial_by_name(message: types.Message, state: FSMContext):
    serial_name = message.text.strip()

    # Serialni bazadan qidirish
    serial = db.get_serial_by_name(serial_name)

    if serial:
        # Serialni bazadan o'chirish
        db.delete_serial_by_name(serial_name)
        await message.answer(f"Serial '{serial_name}' muvaffaqiyatli o'chirildi ✅")
    else:
        await message.answer(f"Serial '{serial_name}' topilmadi ❌")

    # Holatni tozalash
    await state.clear()

