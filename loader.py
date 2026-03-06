from aiogram import Bot, Dispatcher
from data.config import BOT_TOKEN, host, user, password, database
from utils.db_api.mysql import Database
from aiogram.fsm.storage.memory import MemoryStorage


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database(host=host, user=user, password=password, database=database)


async def is_admin(user_id: int) -> bool:
    admin = db.get_admin(user_id)
    return admin is not None
