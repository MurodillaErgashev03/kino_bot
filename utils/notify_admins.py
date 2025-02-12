from loader import db
from loader import bot

# Bot faollashganida adminlarga xabar yuborish funksiyasi
async def start():
    admins = db.get_all_admins()
    for admin in admins:
        try:
            await bot.send_message(chat_id=admin['user_id'], text="Bot faollashdi!")
        except Exception as e:
            print(f"Admin {admin['user_id']} ga xabar yuborishda xatolik: {e}")

# Bot o‘chirilganda adminlarga xabar yuborish funksiyasi
async def shutdown():
    admins = db.get_all_admins()
    for admin in admins:
        try:
            await bot.send_message(chat_id=admin['user_id'], text="Bot to'xtadi!")
        except Exception as e:
            print(f"Admin {admin['user_id']} ga xabar yuborishda xatolik: {e}")
