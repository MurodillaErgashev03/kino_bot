from mailbox import Message

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from filters import IsBotAdmin
from keyboards.inline.buttons import delete_channel_button
from loader import dp, db
from aiogram import types, F

from keyboards.default.buttons import admin_button
from states.film_add_states import FilmAddStates


@dp.message(F.text == "🔙 Orqaga", IsBotAdmin())
async def orqaga(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔝 Asosiy Menyu", reply_markup=admin_button())


@dp.message(F.text == "➕ Kanal qo'shish", IsBotAdmin())
async def add_channel(message: types.Message, state: FSMContext):
    await message.answer("Majburiy obunaga qo'shmoqchi bo'lgan telegram kanaldan biron habarni uzating !")
    await state.set_state(FilmAddStates.chat_id)


@dp.message(FilmAddStates.chat_id, F.forward_from_chat)
async def process_forwarded_message(message: Message, state: FSMContext):
    if message.forward_from_chat.type == "channel":
        channel_id = message.forward_from_chat.id
        channel_username = message.forward_from_chat.username
        if not channel_username:
            await message.answer("Bu yopiq kanal. Iltimos, kanal havolasini yuboring !")
            await state.update_data(channel_id=channel_id)
            await state.set_state(FilmAddStates.waiting_for_channel_link)
        else:
            db.add_kanal(channel_id,"https://t.me/" +channel_username  )
            await message.answer(f"Kanal qo'shildi!\nKanal ID: {channel_id}\nUsername: @{channel_username}")
    else:
        await message.answer("Iltimos, kanaldan xabar forward qiling.")


@dp.message(FilmAddStates.waiting_for_channel_link)
async def process_channel_link(message: Message, state: FSMContext):
    channel_link = message.text
    data = await state.get_data()
    channel_id = data.get("channel_id")
    db.add_kanal(channel_id, channel_link)
    await message.answer(f"Kanal qo'shildi!\nKanal ID: {channel_id}\nLink: {channel_link}")
    await state.clear()


@dp.message(F.text == "➖ Kanal o'chrish", IsBotAdmin())
async def delete_channel(message: types.Message, state: FSMContext):
    await message.answer("O‘chirmoqchi bo‘lgan kanalingizni ustiga bosing!", reply_markup=await delete_channel_button())


@dp.callback_query(lambda c: c.data.startswith('delete_channel_'))
async def process_channel_deletion(callback_query: CallbackQuery):
    chanal_id = callback_query.data.split('_')[2]
    db.delete_kanal(chanal_id)

    await callback_query.answer("Kanal muvaffaqiyatli o'chirildi!")
    await callback_query.message.edit_text("Tanlangan kanal muvaffaqiyatli o‘chirildi.")


@dp.message(F.text == "👁‍🗨 Majburiy kanallarni ko'rish", IsBotAdmin())
async def list_channels(message: types.Message):
    channels = db.get_all_url()
    if channels:
        # URLni tekshirish va formatlash
        channels_text = "\n\n".join(
            [f"{channel}" if channel.startswith("https://t.me/") else f"https://t.me/{channel}" for channel in channels]
        )
        await message.answer(f"Majburiy kanallar:\n\n{channels_text}")
    else:
        await message.answer("Majburiy kanallar qo'shilmagan.")


