import asyncio
import logging
import sys
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher

from database.engine import create_db, session_maker, drop_db

from filters.admin_filter import AdminFilter
from middlewares.acl import ACLMiddleware
from handlers import user_handler, admin_handler, menu_processing

from config import *
from middlewares.db_middleware import DataBaseSession
from middlewares.album_middleware import AlbumMiddleware
from middlewares.scheduler_middleware import SchedulerMiddleware
from middlewares.throthling import ThrottlingMiddleware


async def on_startup(bot: Bot, dp: Dispatcher, scheduler: AsyncIOScheduler):
    await create_db()
    scheduler.start()
    logging.info('Scheduler started')

async def on_shutdown(bot: Bot, scheduler: AsyncIOScheduler):
    scheduler.shutdown()
    logging.info('Scheduler stopped')
    logging.info('bot is down')



async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    scheduler = AsyncIOScheduler()

    @dp.startup()
    async def startup_handler():
        await on_startup(bot, dp, scheduler)

    @dp.shutdown()
    async def shutdown_handler():
        await on_shutdown(bot, scheduler)

    # Using middlewares
    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    user_handler.user_router.message.middleware(AlbumMiddleware(latency=0.3))
    user_handler.user_router.message.middleware(ACLMiddleware())
    user_handler.user_router.message.middleware(ThrottlingMiddleware())
    user_handler.user_router.message.middleware(SchedulerMiddleware(scheduler))

    # Using filters
    admin_handler.admin_router.message.filter(AdminFilter())

    # Including routers
    admin_handler.admin_router.include_router(menu_processing.main_menu_router)
    dp.include_router(admin_handler.admin_router)
    dp.include_router(user_handler.user_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
