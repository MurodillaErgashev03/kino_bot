#handler/majburiy_obuna.py
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from filters import IsBotAdmin
from keyboards.inline.buttons import delete_channel_button, channel_detail_buttons, view_channels_paginated
from loader import dp, db, bot
from aiogram import types, F

from keyboards.default.buttons import admin_button, choose_subscription_type, choose_channel_add_method, majburiy_obuna
from states.film_add_states import FilmAddStates


@dp.message(F.text == "🔙 Orqaga", IsBotAdmin())
async def orqaga(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔝 Asosiy Menyu", reply_markup=admin_button())


# YANGILANGAN - Kanal qo'shish bo'limi (endi 3 ta variant)
@dp.message(F.text == "➕ Kanal qo'shish", IsBotAdmin())
async def add_subscription_start(message: types.Message):
    await message.answer(
        "Qaysi turdagi obuna qo'shmoqchisiz?",
        reply_markup=choose_subscription_type()
    )


# YANGI - Kanal qo'shish tanlangan
@dp.message(F.text == "📢 Kanal qo'shish", IsBotAdmin())
async def choose_channel_method(message: types.Message):
    await message.answer(
        "Kanalni qanday qo'shmoqchisiz?",
        reply_markup=choose_channel_add_method()
    )


# handlers/users/majburiy_obuna.py

@dp.message(F.text == "👤 Username orqali qo'shish", IsBotAdmin())
async def add_channel_by_username_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Kanal username yoki linkini yuboring:\n\n"
        "📝 Formatlar:\n"
        "• @darkvayb yoki darkvayb (public kanal)\n"
        "• https://t.me/+UCLjH3QI1oQ5ZTli (private kanal)\n\n"
        "⚠️ Bot kanalda admin bo'lishi SHART!"
    )
    await state.set_state(FilmAddStates.waiting_for_channel_username)


@dp.message(FilmAddStates.waiting_for_channel_username, F.text)
async def process_channel_username(message: Message, state: FSMContext):
    username = message.text.strip()

    # PRIVATE KANAL LINK TEKSHIRUVI
    if username.startswith('https://t.me/+') or username.startswith('t.me/+'):
        # Bu private kanal invite link
        channel_url = username if username.startswith('https://') else f"https://{username}"

        # State ga saqlash
        await state.update_data(channel_url=channel_url)

        await message.answer(
            f"✅ Link qabul qilindi: {channel_url}\n\n"
            f"Endi kanalning chat_id sini yuboring:\n\n"
            f"📱 Chat ID ni qanday topish mumkin:\n"
            f"1. Botni kanalga admin qiling\n"
            f"2. @raw_data_bot dan foydalaning\n\n"
            f"Misol: -1002373292625"
        )
        await state.set_state(FilmAddStates.waiting_for_channel_chat_id)
        return

    # PUBLIC KANAL - @ belgisini olib tashlash
    if username.startswith('@'):
        username = username[1:]

    channel_url = f"https://t.me/{username}"

    try:
        # Kanalni tekshirish
        chat = await bot.get_chat(f"@{username}")
        channel_id = str(chat.id)

        # Botning admin ekanligini tekshirish
        bot_member = await bot.get_chat_member(chat.id, bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await message.answer(
                f"⚠️ Bot @{username} kanalida admin emas!\n"
                f"Iltimos, botni avval admin qiling, keyin qayta urinib ko'ring.",
                reply_markup=majburiy_obuna()
            )
            await state.clear()
            return

        # Bazaga saqlash
        db.add_kanal(channel_id, channel_url, 'channel')
        await message.answer(
            f"✅ Kanal muvaffaqiyatli qo'shildi!\n"
            f"Kanal: @{username}\n"
            f"ID: {channel_id}",
            reply_markup=majburiy_obuna()
        )
    except Exception as e:
        await message.answer(
            f"❌ Xatolik yuz berdi: {str(e)}\n\n"
            f"Iltimos, kanal username'ini to'g'ri kiriting va botni kanalga admin qiling!",
            reply_markup=majburiy_obuna()
        )

    await state.clear()


# YANGI HANDLER - Private kanal uchun chat_id qabul qilish
@dp.message(FilmAddStates.waiting_for_channel_chat_id, F.text)
async def process_channel_chat_id(message: Message, state: FSMContext):
    chat_id_text = message.text.strip()

    # Chat ID ni tekshirish
    try:
        # Chat ID raqam bo'lishi kerak
        chat_id = int(chat_id_text)

        # Kanal chat_id manfiy bo'lishi kerak
        if chat_id >= 0:
            await message.answer(
                "❌ Kanal chat_id manfiy bo'lishi kerak!\n\n"
                "Misol: -1002373292625\n\n"
                "Iltimos, to'g'ri chat_id yuboring:",
                reply_markup=majburiy_obuna()
            )
            return

    except ValueError:
        await message.answer(
            "❌ Chat ID faqat raqamlardan iborat bo'lishi kerak!\n\n"
            "Misol: -1002373292625\n\n"
            "Iltimos, qaytadan yuboring:",
            reply_markup=majburiy_obuna()
        )
        return

    # State dan URL ni olish
    data = await state.get_data()
    channel_url = data.get('channel_url')

    # Botning admin ekanligini tekshirish
    try:
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await message.answer(
                f"⚠️ Bot bu kanalda admin emas!\n\n"
                f"Iltimos:\n"
                f"1. Botni kanalga admin qiling\n"
                f"2. Qaytadan chat_id yuboring yoki /start ni bosing",
                reply_markup=majburiy_obuna()
            )
            return
    except Exception as e:
        await message.answer(
            f"❌ Xatolik: {str(e)}\n\n"
            f"Iltimos:\n"
            f"1. Chat ID to'g'ri ekanligini tekshiring\n"
            f"2. Botni kanalga admin qiling\n"
            f"3. Qaytadan urinib ko'ring",
            reply_markup=majburiy_obuna()
        )
        await state.clear()
        return

    # Kanal nomini olish
    try:
        chat_info = await bot.get_chat(chat_id)
        channel_title = chat_info.title
    except:
        channel_title = "Kanal"

    # Bazaga saqlash
    try:
        db.add_kanal(str(chat_id), channel_url, 'channel')
        await message.answer(
            f"✅ Kanal muvaffaqiyatli qo'shildi!\n\n"
            f"📢 Kanal: {channel_title}\n"
            f"🆔 Chat ID: {chat_id}\n"
            f"🔗 Link: {channel_url}",
            reply_markup=majburiy_obuna()
        )
        await state.clear()
    except Exception as e:
        await message.answer(
            f"❌ Bazaga saqlashda xatolik: {str(e)}",
            reply_markup=majburiy_obuna()
        )
        await state.clear()

# YANGI - Kanal habari orqali qo'shish (eski usul)
@dp.message(F.text == "📨 Kanal habari orqali qo'shish", IsBotAdmin())
async def add_channel_by_forward_start(message: types.Message, state: FSMContext):
    await message.answer("Majburiy obunaga qo'shmoqchi bo'lgan telegram kanaldan biron habarni uzating!")
    await state.set_state(FilmAddStates.chat_id)


@dp.message(FilmAddStates.chat_id, F.forward_from_chat)
async def process_forwarded_message(message: Message, state: FSMContext):
    if message.forward_from_chat.type == "channel":
        channel_id = message.forward_from_chat.id
        channel_username = message.forward_from_chat.username
        if not channel_username:
            await message.answer("Bu yopiq kanal. Iltimos, kanal havolasini yuboring!")
            await state.update_data(channel_id=channel_id)
            await state.set_state(FilmAddStates.waiting_for_channel_link)
        else:
            db.add_kanal(str(channel_id), "https://t.me/" + channel_username, 'channel')
            await message.answer(
                f"✅ Kanal qo'shildi!\n"
                f"Kanal ID: {channel_id}\n"
                f"Username: @{channel_username}",
                reply_markup=majburiy_obuna()
            )
            await state.clear()
    else:
        await message.answer("Iltimos, kanaldan xabar forward qiling.")


@dp.message(FilmAddStates.waiting_for_channel_link)
async def process_channel_link(message: Message, state: FSMContext):
    channel_link = message.text
    data = await state.get_data()
    channel_id = data.get("channel_id")
    db.add_kanal(str(channel_id), channel_link, 'channel')
    await message.answer(
        f"✅ Kanal qo'shildi!\n"
        f"Kanal ID: {channel_id}\n"
        f"Link: {channel_link}",
        reply_markup=majburiy_obuna()
    )
    await state.clear()


@dp.message(F.text == "👥 Guruh qo'shish", IsBotAdmin())
async def add_group_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Guruh linkini yuboring:\n\n"
        "📝 Formatlar:\n"
        "• https://t.me/mygroup (public guruh)\n"
        "• https://t.me/+RtsVgjInu1k1NGFi (private guruh)\n\n"
        "⚠️ Bot guruhda admin bo'lishi SHART!"
    )
    await state.set_state(FilmAddStates.waiting_for_group_url)


@dp.message(FilmAddStates.waiting_for_group_url, F.text)
async def process_group_url(message: Message, state: FSMContext):
    group_url = message.text.strip()

    # Link formatini tekshirish
    if not (group_url.startswith('https://t.me/') or group_url.startswith('t.me/')):
        await message.answer(
            "❌ Noto'g'ri link formati!\n\n"
            "To'g'ri formatlar:\n"
            "• https://t.me/mygroup\n"
            "• https://t.me/+RtsVgjInu1k1NGFi\n\n"
            "Iltimos, qaytadan yuboring:",
            reply_markup=majburiy_obuna()
        )
        return

    # https:// qo'shish (agar yo'q bo'lsa)
    if not group_url.startswith('https://'):
        group_url = f"https://{group_url}"

    # State ga saqlash
    await state.update_data(group_url=group_url)

    await message.answer(
        f"✅ Link qabul qilindi: {group_url}\n\n"
        f"Endi guruhning chat_id sini yuboring:\n\n"
        f"📱 Chat ID ni @raw_data_bot orqali oling\n"
    )
    await state.set_state(FilmAddStates.waiting_for_group_chat_id)


@dp.message(FilmAddStates.waiting_for_group_chat_id, F.text)
async def process_group_chat_id(message: Message, state: FSMContext):
    chat_id_text = message.text.strip()

    # Chat ID ni tekshirish
    try:
        # Chat ID raqam bo'lishi kerak
        chat_id = int(chat_id_text)

        # Guruh chat_id manfiy bo'lishi kerak
        if chat_id >= 0:
            await message.answer(
                "❌ Guruh chat_id manfiy bo'lishi kerak!\n\n"
                "Misol: -1002373292625\n\n"
                "Iltimos, to'g'ri chat_id yuboring:",
                reply_markup=majburiy_obuna()
            )
            return

    except ValueError:
        await message.answer(
            "❌ Chat ID faqat raqamlardan iborat bo'lishi kerak!\n\n"
            "Misol: -1002373292625\n\n"
            "Iltimos, qaytadan yuboring:",
            reply_markup=majburiy_obuna()
        )
        return

    # State dan URL ni olish
    data = await state.get_data()
    group_url = data.get('group_url')

    # Botning admin ekanligini tekshirish
    try:
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await message.answer(
                f"⚠️ Bot bu guruhda admin emas!\n\n"
                f"Iltimos:\n"
                f"1. Botni guruhga admin qiling\n"
                f"2. Qaytadan chat_id yuboring yoki /start ni bosing",
                reply_markup=majburiy_obuna()
            )
            return
    except Exception as e:
        await message.answer(
            f"❌ Xatolik: {str(e)}\n\n"
            f"Iltimos:\n"
            f"1. Chat ID to'g'ri ekanligini tekshiring\n"
            f"2. Botni guruhga admin qiling\n"
            f"3. Qaytadan urinib ko'ring",
            reply_markup=majburiy_obuna()
        )
        await state.clear()
        return

    # Guruh nomini olish
    try:
        chat_info = await bot.get_chat(chat_id)
        group_title = chat_info.title
    except:
        group_title = "Guruh"

    # Bazaga saqlash
    try:
        db.add_kanal(str(chat_id), group_url, 'group')
        await message.answer(
            f"✅ Guruh muvaffaqiyatli qo'shildi!\n\n"
            f"📱 Guruh: {group_title}\n"
            f"🆔 Chat ID: {chat_id}\n"
            f"🔗 Link: {group_url}",
            reply_markup=majburiy_obuna()
        )
        await state.clear()
    except Exception as e:
        await message.answer(
            f"❌ Bazaga saqlashda xatolik: {str(e)}",
            reply_markup=majburiy_obuna()
        )
        await state.clear()

# YANGI - Instagram akkaunt qo'shish
@dp.message(F.text == "📸 Instagram akkaunt qo'shish", IsBotAdmin())
async def add_instagram_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Instagram akkaunt username'ini yuboring (masalan: hikmatillo.5)\n\n"
        "ℹ️ Faqat username kiriting, @ yoki link kerak emas!"
    )
    await state.set_state(FilmAddStates.waiting_for_instagram_username)


@dp.message(FilmAddStates.waiting_for_instagram_username, F.text)
async def process_instagram_username(message: Message, state: FSMContext):
    username = message.text.strip()

    # @ belgisini olib tashlash
    if username.startswith('@'):
        username = username[1:]

    # Link formatiga keltirish
    instagram_url = f"https://www.instagram.com/{username}/"

    # Chat_id sifatida username dan foydalanish (Instagram uchun telegram chat_id yo'q)
    # Biror unique identifier kerak, shuning uchun username ni ishlatamiz
    chat_id = f"instagram_{username}"

    try:
        # Bazaga saqlash
        db.add_kanal(chat_id, instagram_url, 'instagram')
        await message.answer(
            f"✅ Instagram akkaunt muvaffaqiyatli qo'shildi!\n"
            f"Username: {username}\n"
            f"Link: {instagram_url}",
            reply_markup=majburiy_obuna()
        )
    except Exception as e:
        await message.answer(
            f"❌ Xatolik yuz berdi: {str(e)}\n\n"
            f"Iltimos, qayta urinib ko'ring!",
            reply_markup=majburiy_obuna()
        )

    await state.clear()


# Kanal/Guruh/Instagram o'chirish
@dp.message(F.text == "➖ Kanal o'chrish", IsBotAdmin())
async def delete_channel(message: types.Message):
    await message.answer("O'chirmoqchi bo'lgan obunangizni ustiga bosing!", reply_markup=await delete_channel_button())


# handlers/users/majburiy_obuna.py

@dp.callback_query(lambda c: c.data.startswith('delete_channel_'))
async def process_channel_deletion(callback_query: CallbackQuery):
    try:
        # Callback data dan chat_id ni olish
        # Format: delete_channel_{chat_id}

        # "delete_channel_" dan keyingi qismni olish
        chat_id = callback_query.data.replace('delete_channel_', '')

        if not chat_id:
            raise ValueError("Chat ID topilmadi")

        # Ma'lumotlar bazasidan o'chirish
        db.delete_kanal(chat_id)

        print(f"✅ Kanal/Guruh/Instagram o'chirildi: {chat_id}")

        await callback_query.answer("Obuna muvaffaqiyatli o'chirildi!")
        await callback_query.message.edit_text(
            "✅ Tanlangan obuna muvaffaqiyatli o'chirildi!",
            reply_markup=None
        )

    except Exception as e:
        print(f"❌ Obunani o'chirishda xatolik: {str(e)}")
        await callback_query.answer("Xatolik yuz berdi!")
        await callback_query.message.edit_text(
            f"❌ Obunani o'chirishda xatolik: {str(e)}",
            reply_markup=None
        )


@dp.message(F.text == "👁‍🗨 Majburiy kanallarni ko'rish", IsBotAdmin())
async def list_channels_paginated(message: types.Message):
    total = db.count_channels()
    if total == 0:
        await message.answer("Majburiy obunalar qo'shilmagan")
        return

    await message.answer(
        "📋 Majburiy obunalar ro'yxati:\n\n"
        "Kanal ustiga bosing va sozlamalarini o'zgartiring:",
        reply_markup=await view_channels_paginated(page=1)
    )


@dp.callback_query(lambda c: c.data.startswith('ch_page_'))
async def paginate_channels(callback_query: CallbackQuery):
    """Sahifalar orasida o'tish"""
    page = int(callback_query.data.split('_')[2])

    await callback_query.message.edit_text(
        "📋 Majburiy obunalar ro'yxati:\n\n"
        "Kanal ustiga bosing va sozlamalarini o'zgartiring:",
        reply_markup=await view_channels_paginated(page=page)
    )
    await callback_query.answer()


@dp.callback_query(lambda c: c.data.startswith('view_ch_'))
async def show_channel_details(callback_query: CallbackQuery):
    """Kanal tafsilotlarini ko'rsatish"""
    # view_ch_{chat_id} dan chat_id ni olish
    chat_id = callback_query.data.replace('view_ch_', '')

    channels = db.get_all_channels()
    channel_info = None

    for ch in channels:
        if ch['chat_id'] == chat_id:
            channel_info = ch
            break

    if not channel_info:
        await callback_query.answer("Kanal topilmadi!")
        return

    level = channel_info.get('level', 'primary')
    level_text = "1-darajali (Asosiy)" if level == 'primary' else "2-darajali (Qo'shimcha)"
    type_text = {"channel": "Kanal", "group": "Guruh", "instagram": "Instagram"}.get(
        channel_info.get('type', 'channel'), 'Kanal'
    )

    text = (
        f"📊 {type_text} ma'lumotlari:\n\n"
        f"🔗 Link: {channel_info['url']}\n"
        f"📍 Daraja: {level_text}\n"
        f"🆔 Chat ID: {chat_id}\n\n"
        f"Darajani o'zgartiring:"
    )

    await callback_query.message.edit_text(
        text,
        reply_markup=await channel_detail_buttons(chat_id)
    )
    await callback_query.answer()


@dp.callback_query(lambda c: c.data.startswith('set_lvl_'))
async def change_channel_level(callback_query: CallbackQuery):
    """Kanal darajasini o'zgartirish"""
    parts = callback_query.data.split('_')
    new_level = parts[2]  # primary yoki secondary
    chat_id = '_'.join(parts[3:])  # chat_id

    # Bazada yangilash
    db.update_channel_level(chat_id, new_level)

    level_text = "1-darajali" if new_level == 'primary' else "2-darajali"

    await callback_query.answer(f"✅ Daraja o'zgartirildi: {level_text}")

    # Yangilangan ma'lumotlarni ko'rsatish
    channels = db.get_all_channels()
    channel_info = None

    for ch in channels:
        if ch['chat_id'] == chat_id:
            channel_info = ch
            break

    if channel_info:
        type_text = {"channel": "Kanal", "group": "Guruh", "instagram": "Instagram"}.get(
            channel_info.get('type', 'channel'), 'Kanal'
        )

        text = (
            f"📊 {type_text} ma'lumotlari:\n\n"
            f"🔗 Link: {channel_info['url']}\n"
            f"📍 Daraja: {level_text}\n"
            f"🆔 Chat ID: {chat_id}\n\n"
            f"Darajani o'zgartiring:"
        )

        await callback_query.message.edit_text(
            text,
            reply_markup=await channel_detail_buttons(chat_id)
        )


@dp.callback_query(lambda c: c.data == 'back_to_ch_list')
async def back_to_channels_list(callback_query: CallbackQuery):
    """Kanallar ro'yxatiga qaytish"""
    await callback_query.message.edit_text(
        "📋 Majburiy obunalar ro'yxati:\n\n"
        "Kanal ustiga bosing va sozlamalarini o'zgartiring:",
        reply_markup=await view_channels_paginated(page=1)
    )
    await callback_query.answer()


@dp.callback_query(lambda c: c.data == 'ignore')
async def ignore_callback(callback_query: CallbackQuery):
    """Sahifa raqami tugmasini ignore qilish"""
    await callback_query.answer()