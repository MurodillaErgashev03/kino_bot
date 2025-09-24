from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from filters import IsBotAdmin
from keyboards.default.buttons import admin_button
from keyboards.inline.buttons import delete_admin_button
from loader import dp, db
from aiogram import types, F

from states.film_add_states import FilmAddStates

@dp.message(F.text == "🔙 Orqaga", IsBotAdmin())
async def orqaga(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔝 Asosiy Menyu", reply_markup=admin_button())

@dp.message(F.text == "👁‍🗨 Adminlarni ko'rish", IsBotAdmin())
async def list_channels(message: types.Message):
    admins = db.get_all_admins()
    if admins:
        channels_text = "\n\n".join(
            [f"{admin['user_name']}" if admin['user_name'].startswith("") else f"{admin['user_name']}" for admin in admins]
        )
        await message.answer(f"Adminlar:\n\n{channels_text}")

@dp.message(F.text == "➕ Admin qo'shish", IsBotAdmin())
async def add_admin(message: types.Message, state: FSMContext):
    await message.answer("Yangi Adminni biron xabarni Forward qiling !")
    await state.set_state(FilmAddStates.admin_chat_id)

@dp.message(FilmAddStates.admin_chat_id)
async def add_admin(message: types.Message,state:FSMContext):
    if message.forward_from:
        admin_chat_id = message.forward_from.id
        admin_name = message.forward_from.full_name

        db.add_admin(admin_chat_id, admin_name)

        await message.answer(f"✅ {admin_name}\n<b>ID:</b> <code>{admin_chat_id}</code> admin sifatida qo'shildi!")
        await state.clear()
    else:
        await message.answer(
            "❌ Xatolik: Iltimos, faqat foydalanuvchi profilidan xabar forward qiling.\n\nKanaldan yoki maxfiyligini sozlagan foydalanuvchidan forward qilib bo'lmaydi.")


@dp.message(F.text == "➖ Admin o'chrish", IsBotAdmin())
async def delete_admin(message: types.Message, state: FSMContext):
    await message.answer("O‘chirmoqchi bo‘lgan adminingizni tanlang!", reply_markup=await delete_admin_button())
    await state.set_state(FilmAddStates.admin_chat_id)


@dp.callback_query(lambda c: c.data.startswith('delete_admin_'))
async def process_admin_deletion(callback_query: CallbackQuery):
    try:
        user_id = callback_query.data.split('_')[2]  # Callback'dan user_id ni olish
        if not user_id:
            raise ValueError("User ID topilmadi")

        db.delete_admin_id(user_id)  # Ma'lumotlar bazasidan adminni o'chirish

        await callback_query.answer("Admin safidan badarg'a qilindi!")
        await callback_query.message.edit_text("Admin safidan badarg'a qilindi!")

    except Exception as e:
        await callback_query.answer("Xatolik yuz berdi!")
        await callback_query.message.edit_text(f"Adminni o'chirishda xatolik: {str(e)}")


@dp.message(F.text == "👁‍🗨 Adminlarni ko'rish", IsBotAdmin())
async def list_channels(message: types.Message):
    admins = db.get_all_admins()
    if admins:
        channels_text = "\n\n".join(
            [f"{admin['user_name']}" if admin['user_name'].startswith("") else f"{admin['user_name']}" for admin in admins]
        )
        await message.answer(f"Adminlar:\n\n{channels_text}")

