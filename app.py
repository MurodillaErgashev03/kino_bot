from loader import dp, bot, db
import asyncio

from handlers import admin_router, user_router
from middlewares.subscription_middleware import UserCheckMiddleware
from utils.notify_admins import start, shutdown

import logging
import sys


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        dp.startup.register(start)
        dp.shutdown.register(shutdown)
        dp.update.outer_middleware(UserCheckMiddleware())

        # Routerlarni ulash (tartib muhim: admin birinchi, user oxirida)
        dp.include_router(admin_router)
        dp.include_router(user_router)

        # Jadvallarni yaratish
        for create_func in [
            db.create_table_admins,
            db.create_table_users,
            db.create_table_kanal,
            db.create_table_data,
            db.create_table_serials,
            db.create_table_episodes,
        ]:
            try:
                create_func()
            except Exception as e:
                print(e)

        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
