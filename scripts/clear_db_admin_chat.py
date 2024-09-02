from datetime import datetime, timedelta
import logging

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.base import StorageKey
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import ADMIN_USER_ID, TEXT_MESSAGES, MESSAGE_LIFETIME_HOURS, MESSAGE_LIFETIME_SECONDS
from database.orm_query import orm_get_and_delete_all_suggestions, orm_extract_suggestions
from keyboards.inline import create_ok_menu


async def delete_messages_and_record(bot: Bot, session, message_ids, suggestion_id):
    try:
        # Clear db
        suggestions = await orm_extract_suggestions(session, suggestion_id)

        # Clear basic messages
        await bot.delete_messages(chat_id=ADMIN_USER_ID, message_ids=message_ids)

        # Clear help message;
        # The id value for help_message is the same for all records in db, it is enough to delete the chat message once
        await bot.delete_message(chat_id=ADMIN_USER_ID, message_id=suggestions[0].help_message)

    except Exception as e:
        logging.error(f"Error deleting a message and record: {e}")


async def schedule_message_deletion(bot, session, message_ids: list, suggestion_id, scheduler: AsyncIOScheduler):
    #  plan to delete the message in 47 hours
    run_time = datetime.now() + timedelta(hours=MESSAGE_LIFETIME_HOURS, seconds=MESSAGE_LIFETIME_SECONDS)
    scheduler.add_job(
        delete_messages_and_record,
        trigger='date',
        run_date=run_time,
        args=[bot, session, message_ids, suggestion_id]
    )


# async def clear_db_admin_chat(bot, session_pool, dp: Dispatcher):
#     """Clears the admin chat and the database at a set time once a day."""
#     async with session_pool() as session:
#         cleared = False
#         try:
#             suggestions = await orm_get_and_delete_all_suggestions(session)
#
#             suggestions_ids = list((suggestion.mess_id for suggestion in suggestions))
#             help_message_ids = list((suggestion.help_message for suggestion in suggestions))
#
#             if suggestions_ids and help_message_ids:
#                 await bot.delete_messages(chat_id=ADMIN_USER_ID, message_ids=suggestions_ids)
#                 await bot.delete_messages(chat_id=ADMIN_USER_ID, message_ids=help_message_ids)
#                 cleared = True
#
#             # Use FSMContext to reset the state\
#             bot_info = await bot.get_me()
#             bot_id = bot_info.id
#             storage_key = StorageKey(
#                 chat_id=int(ADMIN_USER_ID),
#                 user_id=int(ADMIN_USER_ID),
#                 bot_id=bot_id
#             )
#             await dp.storage.set_state(storage_key, state=None)
#             await dp.storage.set_data(storage_key, data={})
#
#             logging.info(f"Chat has been cleared at{datetime.now().time()}")
#         except Exception as e:
#             logging.exception(e)
#
#         if cleared:
#             # Send a confirmation message
#             await bot.send_message(
#                 chat_id=ADMIN_USER_ID,
#                 text=TEXT_MESSAGES['cleared'],
#                 reply_markup=create_ok_menu()
#             )
#         else:
#             await bot.send_message(
#                 chat_id=ADMIN_USER_ID,
#                 text=TEXT_MESSAGES['not_cleared'],
#                 reply_markup=create_ok_menu()
#             )