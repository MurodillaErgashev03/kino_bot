from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from filters import IsBotAdmin
from keyboards.inline.buttons import delete_admin_button
from handlers.admin import admin_router
from loader import db
from aiogram import types, F
from states.states import AdminStates


@admin_router.message(F.text == "👁‍🗨 Adminlarni ko'rish", IsBotAdmin())
async def list_admins(message: types.Message):
    admins = db.get_all_admins()
    if admins:
        channels_text = "\n\n".join(
            [f"{admin['user_name']}" for admin in admins]
        )
        await message.answer(f"Adminlar:\n\n{channels_text}")
    else:
        await message.answer("Hozircha adminlar yo'q.")


@admin_router.message(F.text == "➕ Admin qo'shish", IsBotAdmin())
async def add_admin_start(message: types.Message, state: FSMContext):
    await message.answer("Yangi Adminni biron xabarni Forward qiling !")
    await state.set_state(AdminStates.admin_chat_id)


@admin_router.message(AdminStates.admin_chat_id)
async def add_admin_process(message: types.Message, state: FSMContext):
    if message.forward_from:
        admin_chat_id = message.forward_from.id
        admin_name = message.forward_from.full_name

        if message.forward_from.is_bot:
            await message.answer("Xabarni botdan forward qilmang. Faqat haqiqiy foydalanuvchidan forward qiling.")
            return

    elif message.forward_from_chat:
        await message.answer(
            "Bu xabar kanaldan/guruhdan forward qilingan. Admin qo'shish uchun shaxsiy foydalanuvchi xabarini forward qiling.")
        return

    else:
        await message.answer(
            "Kechirasiz, bu foydalanuvchining shaxsiy sozlamalari ularning ID'sini forward qilishga ruxsat bermaydi. "
            "Iltimos, boshqa foydalanuvchidan forward qiling yoki ulardan sozlamalarini tekshirishni so'rang.")
        return

    db.add_admin(str(admin_chat_id), admin_name)

    await message.answer(f"✅ {admin_name}\nID: {admin_chat_id} admin sifatida qo'shildi!")
    await state.clear()


@admin_router.message(F.text == "➖ Admin o'chrish", IsBotAdmin())
async def delete_admin(message: types.Message, state: FSMContext):
    await message.answer("O'chirmoqchi bo'lgan adminingizni tanlang!", reply_markup=await delete_admin_button())


@admin_router.callback_query(lambda c: c.data.startswith('delete_admin_'))
async def process_admin_deletion(callback_query: CallbackQuery):
    try:
        user_id = callback_query.data.split('_')[2]
        if not user_id:
            raise ValueError("User ID topilmadi")

        db.delete_admin_id(user_id)

        await callback_query.answer("Admin safidan badarg'a qilindi!")
        await callback_query.message.edit_text("Admin safidan badarg'a qilindi!")

    except Exception as e:
        await callback_query.answer("Xatolik yuz berdi!")
        await callback_query.message.edit_text(f"Adminni o'chirishda xatolik: {str(e)}")
