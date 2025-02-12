from aiogram.types import CallbackQuery
from filters import IsBotAdmin
from keyboards.inline.buttons import generate_episode_buttons, yes_no_button_episode, yes_no_button_confirmation, add_episode_button
from loader import dp, db
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from states.film_add_states import FilmAddStates
from utils.db_api.mysql import logger


# Yangi serial qo'shish boshlang'ich handleri
@dp.message(F.text == "➕ Yangi serial joylash", IsBotAdmin())
async def serial_add_start(message: types.Message, state: FSMContext):
    await message.answer("Serial kodi!")
    await state.set_state(FilmAddStates.waiting_for_serial_name)


# Serial nomini kiritish
@dp.message(FilmAddStates.waiting_for_serial_name, F.text)
async def serial_name_add(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if db.check_code_exists_serial(name):
        await message.answer("Bu nom allaqachon mavjud. Iltimos, boshqa nom kiriting!")
    else:
        await state.update_data({'serial_name': name, 'episodes': []})
        await message.answer("Serial haqida:")
        await state.set_state(FilmAddStates.waiting_for_serial_title)


# Serial haqida matnni kiritish
@dp.message(FilmAddStates.waiting_for_serial_title, F.text)
async def serial_title_add(message: types.Message, state: FSMContext):
    serial_title = message.text.strip()
    await state.update_data({'serial_title': serial_title})
    await message.answer("Serial banneri uchun rasm jo'nating!")
    await state.set_state(FilmAddStates.waiting_for_serial_banner)


# Serial bannerini qabul qilish
@dp.message(FilmAddStates.waiting_for_serial_banner, F.photo)
async def serial_banner_add(message: types.Message, state: FSMContext):
    try:
        photo = message.photo[-1]
        file_id = photo.file_id
        await state.update_data({'serial_banner': file_id})
        await message.answer("Serial qismi uchun videoni jo'nating!")
        await state.set_state(FilmAddStates.waiting_for_episode_video)
    except Exception as e:
        await message.answer("Rasmni yuklashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        await state.clear()
        logger(str(e))


# Yangi serial uchun epizod qo'shish
@dp.message(FilmAddStates.waiting_for_episode_video, F.video)
async def episode_video_add_new_serial(message: types.Message, state: FSMContext):
    try:
        video = message.video
        video_id = video.file_id
        data = await state.get_data()
        episodes = data.get('episodes', [])
        episode_number = len(episodes) + 1
        episodes.append({'episode_number': episode_number, 'video_id': video_id})
        await state.update_data({'episodes': episodes})
        await message.answer(
            f"Serial qismi {episode_number} qo'shildi!\nYana qism qo'shishni xohlaysizmi? (Ha/Yo'q)",
            reply_markup=await yes_no_button_episode()
        )
        await state.set_state(FilmAddStates.waiting_for_more_episodes)
    except Exception as e:
        await message.answer("Video qo'shishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        await state.clear()
        logger(str(e))


# Yangi serial uchun epizod qo'shishni boshqarish (Ha/Yo'q)
@dp.callback_query(FilmAddStates.waiting_for_more_episodes, F.data.in_(['yes_episode', 'no_episode']))
async def more_episodes_decision_new_serial(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == 'yes_episode':
        await callback_query.message.answer("Serial qismi uchun videoni jo'nating!")
        await state.set_state(FilmAddStates.waiting_for_episode_video)
    elif callback_query.data == 'no_episode':
        data = await state.get_data()
        serial_name = data.get('serial_name')
        serial_banner = data.get('serial_banner')
        serial_title = data.get('serial_title')
        episodes = data.get('episodes', [])

        if episodes:
            episodes_list = "\n".join([f"Qism {ep['episode_number']}" for ep in episodes])
        else:
            await callback_query.message.answer("Qismlar yo'q.")

        await callback_query.message.answer(
            f"{serial_name} Serial saqlaysizmi?",
            reply_markup=await yes_no_button_confirmation())
        await state.set_state(FilmAddStates.waiting_for_confirmation)

    await callback_query.answer()


# Yangi serialni tasdiqlash va bazaga saqlash
@dp.callback_query(FilmAddStates.waiting_for_confirmation, F.data.in_(['confirm_yes', 'confirm_no']))
async def confirmation_callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    answer = callback_query.data
    if answer == 'confirm_yes':
        data = await state.get_data()
        serial_name = data.get('serial_name')
        serial_banner = data.get('serial_banner')
        serial_title = data.get('serial_title')
        episodes = data.get('episodes', [])

        try:
            # Serialni bazaga qo'shish
            db.add_serial(serial_name, serial_title, serial_banner)
            serial_id = db.get_serial_id(serial_name)

            if serial_id is None:
                raise ValueError(f"Serial ID topilmadi uchun serial_name: {serial_name}")

            # Epizodlarni bazaga qo'shish
            for ep in episodes:
                db.add_episode(serial_id, ep['episode_number'], ep['video_id'])

            await callback_query.message.answer("Serial va qismlar muvaffaqiyatli saqlandi!")
            await state.clear()
        except Exception as e:
            await callback_query.message.answer("Serial va qismlarni saqlashda xatolik yuz berdi.")
            await state.clear()
            logger(f"Serial va qismlarni saqlashda xatolik: {str(e)}")
    elif answer == 'confirm_no':
        await callback_query.message.answer("Serial qo'shilmadi!")
        await state.clear()

    await callback_query.answer()


# Mavjud serialga epizod qo'shish boshlash
@dp.message(F.text == "➕ Serialning qismlarini qo'shish", IsBotAdmin())
async def start_add_episodes_existing(message: types.Message, state: FSMContext):
    await message.answer("Qaysi serialga qo'shishni tanlang!", reply_markup=await add_episode_button())


# Mavjud serialga epizod qo'shish uchun serial tanlash
@dp.callback_query(lambda c: c.data.startswith('add_episode_'))
async def process_add_episode_existing(callback_query: CallbackQuery, state: FSMContext):
    serial_id = int(callback_query.data.split('_')[2])

    # Bazadan ushbu serial uchun mavjud eng katta epizod raqamini olish
    episodes = db.get_episodes_by_serial_id(serial_id)
    if episodes:
        max_episode_number = max(ep['episode_number'] for ep in episodes)
    else:
        max_episode_number = 0  # Agar epizodlar bo'lmasa, 0 ga tenglaymiz

    # Ushbu ma'lumotlarni holatga saqlaymiz
    await state.update_data({
        'serial_id': serial_id,
        'episodes': [],
        'max_episode_number': max_episode_number
    })

    await callback_query.message.answer("Yangi epizod uchun videoni jo'nating!")
    await state.set_state(FilmAddStates.waiting_for_episode_video_existing)
    await callback_query.answer()


# Mavjud serial uchun epizod qo'shish
@dp.message(FilmAddStates.waiting_for_episode_video_existing, F.video)
async def episode_video_add_existing(message: types.Message, state: FSMContext):
    try:
        video = message.video
        video_id = video.file_id
        data = await state.get_data()
        episodes = data.get('episodes', [])
        max_episode_number = data.get('max_episode_number', 0)

        episode_number = max_episode_number + len(episodes) + 1

        episodes.append({'episode_number': episode_number, 'video_id': video_id})
        await state.update_data({'episodes': episodes})
        await message.answer(
            f"{episode_number}-qism qo'shildi!\nYana qism qo'shishni xohlaysizmi?",
            reply_markup=await yes_no_button_episode()
        )
        await state.set_state(FilmAddStates.waiting_for_more_episodes_existing_serial)
    except Exception as e:
        await message.answer("Video qo'shishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        await state.clear()
        logger(str(e))


# Mavjud serial uchun epizod qo'shishni boshqarish (Ha/Yo'q)
@dp.callback_query(FilmAddStates.waiting_for_more_episodes_existing_serial, F.data.in_(['yes_episode', 'no_episode']))
async def more_episodes_decision_existing(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == 'yes_episode':
        await callback_query.message.answer("Yangi epizod uchun videoni jo'nating!")
        await state.set_state(FilmAddStates.waiting_for_episode_video_existing)
    elif callback_query.data == 'no_episode':
        data = await state.get_data()
        logger(f"State data (Existing Serial): {data}")  # State dagi ma'lumotlarni chiqaramiz
        episodes = data.get('episodes', [])
        serial_id = data.get('serial_id')

        if serial_id is None:
            await callback_query.message.answer("Xatolik yuz berdi: serial aniqlanmadi.")
            await state.clear()
            logger("Error: serial_id is None in state data.")
            return

        # Serial nomini ma'lumotlar bazasidan olib kelish
        serial = db.get_serial_by_id(serial_id)
        if not serial:
            await callback_query.message.answer("Serial topilmadi.")
            await state.clear()
            logger(f"Serial with ID {serial_id} not found.")
            return

        serial_name = serial.get('serial_name', 'Unknown Serial')

        if episodes:
            # Epizodlarni bazaga qo'shish
            try:
                for ep in episodes:
                    episode_number = ep['episode_number']
                    video_id = ep['video_id']
                    db.add_episode(serial_id, episode_number, video_id)

                await callback_query.message.answer("Barcha epizodlar muvaffaqiyatli saqlandi!")
                await state.clear()
            except Exception as e:
                await callback_query.message.answer("Epizodlarni saqlashda xatolik yuz berdi.")
                await state.clear()
                logger(f"Epizodlarni saqlashda xatolik: {str(e)}")
        else:
            await callback_query.message.answer("Hech qanday epizod qo'shilmagan.")
            await state.clear()

        # await callback_query.message.answer(
        #     f"{serial_name} Serialni saqlaysizmi?",
        #     reply_markup=await yes_no_button_confirmation())

    await callback_query.answer()


# Epizodni ko'rish
@dp.callback_query(F.data.startswith("view_episode_"))
async def view_episode(callback_query: types.CallbackQuery):
    data_parts = callback_query.data.split("_")
    serial_id = int(data_parts[2])  # 'view_episode_{serial_id}_{episode_number}'
    episode_number = int(data_parts[3])
    await callback_query.answer()

    # Bazadan epizodlarni olish
    episodes = db.get_episodes_by_serial_id(serial_id)

    # Epizodni topish va video yuborish
    for ep in episodes:
        if ep['episode_number'] == episode_number:
            await callback_query.message.answer_video(video=ep['video_id'],
                                                      caption=f"{episode_number}-qism")
            return

    # Agar epizod topilmasa
    await callback_query.message.answer("Epizod topilmadi.")


# Pagination handler
@dp.callback_query(F.data.startswith("pagination_"))
async def pagination_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    data_parts = callback_query.data.split("_")
    serial_id = int(data_parts[1])
    page = int(data_parts[2])
    # Bazadan epizodlarni olish
    episodes = db.get_episodes_by_serial_id(serial_id)
    if not episodes:
        await callback_query.message.answer("Hozircha epizodlar mavjud emas.")
        return

    # Sahifalangan qismlar ro'yxatini qayta chiqarish
    await callback_query.message.edit_reply_markup(reply_markup=generate_episode_buttons(episodes, serial_id, page))
