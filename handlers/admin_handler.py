import logging

from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_user, orm_unblock_user, orm_get_banned_users, orm_get_and_delete_all_suggestions
from keyboards.inline import create_ok_menu
from keyboards.reply import admin_reply_keyboard

from config import TEXT_MESSAGES

admin_router = Router()


@admin_router.message(CommandStart())
async def admin_start(message: Message):
    await message.answer(TEXT_MESSAGES['admin_start'], reply_markup=admin_reply_keyboard())


@admin_router.message(Command('banlist'))
@admin_router.message(F.text == TEXT_MESSAGES['banlist'])
async def show_banlist(message: Message, session: AsyncSession):
    text = TEXT_MESSAGES['list_of_banned'] + ":\n"
    banned_users = await orm_get_banned_users(session)

    for user in banned_users:
        text += f"[{user.user_id}](tg://user?id={user.user_id})\n"


    text += "\n" + TEXT_MESSAGES['to_unblock_enter']

    await message.delete()
    await message.answer(text, parse_mode="Markdown", reply_markup=create_ok_menu())


@admin_router.callback_query(F.data == 'delete_mes')
async def close_message(callback_query: CallbackQuery):
    await callback_query.message.delete()
    await callback_query.answer()


@admin_router.message(Command('unblock'))
async def unblock(message: Message, session: AsyncSession, command: CommandObject):
    await message.delete()

    text = ""
    if command.args is None:
        text += TEXT_MESSAGES['no_args']
    else:
        try:
            user_id = int(command.args)
        except ValueError:
            text = TEXT_MESSAGES['invalid_args']

        else:
            try:
                user = await orm_get_user(session, user_id)
                if user:
                    if await orm_unblock_user(session, user_id):
                        text = TEXT_MESSAGES['has_unbanned']
                    else:
                        text = TEXT_MESSAGES['failed_unban']
                else:
                    text = TEXT_MESSAGES['user_is_not_registered']
            except Exception as e:
                text = TEXT_MESSAGES['user_is_not_registered']
                logging.exception(f"Error fetching user:", exc_info=e)

    await message.answer(text=text, reply_markup=create_ok_menu())


@admin_router.message(Command('rm'))
@admin_router.message(F.text == TEXT_MESSAGES['rm'])
async def admin_remove_chat(message: Message, session: AsyncSession, state: FSMContext):
    await message.delete()

    suggestions = await orm_get_and_delete_all_suggestions(session)

    suggestions_ids = list((suggestion.mess_id for suggestion in suggestions))
    help_message_ids = list((suggestion.help_message for suggestion in suggestions))

    if suggestions_ids and help_message_ids:
        await message.bot.delete_messages(chat_id=message.chat.id, message_ids=suggestions_ids)
        await message.bot.delete_messages(chat_id=message.chat.id, message_ids=help_message_ids)

    await state.clear()

