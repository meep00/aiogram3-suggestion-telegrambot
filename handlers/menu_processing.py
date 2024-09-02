import logging

from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from config import TEXT_MESSAGES, CHANNEL_ID
from database.orm_query import orm_extract_suggestions, orm_block_user_by_sug_id, orm_get_suggestions, \
    orm_update_caption
from keyboards.inline import create_edit_menu_keyboard, create_main_menu_keyboard, MenuCallBack, create_ok_menu
from aiogram.fsm.context import FSMContext

main_menu_router = Router()


class EditMessage(StatesGroup):
    edit_text = State()


@main_menu_router.callback_query(MenuCallBack.filter(F.data == "post"))
async def post_in_the_channel(query: CallbackQuery, session: AsyncSession, callback_data: MenuCallBack):
    suggestion_id = callback_data.suggestion_id

    suggestions = await orm_extract_suggestions(session, suggestion_id)
    suggestions.sort(key=lambda x: x.id)

    if len(suggestions) == 1:
        # An option if you need to send one text message or a message with one photo
        await query.bot.copy_message(chat_id=CHANNEL_ID,
                                     from_chat_id=query.from_user.id,
                                     message_id=suggestions[0].mess_id)
        await query.bot.delete_message(chat_id=query.from_user.id, message_id=suggestions[0].mess_id)
    else:
        # An option if you need to send album of photos
        # A new media group is being formed based on information from the database
        caption = suggestions[0].caption
        entities = suggestions[0].entities
        media_group = [InputMediaPhoto(media=suggestion.file_id,
                                       caption=caption if idx == 0 else '',
                                       caption_entities=entities if idx == 0 else None
                                       )
                       for idx, suggestion in enumerate(suggestions)]
        await query.bot.send_media_group(CHANNEL_ID, media_group)
        for suggestion in suggestions:
            await query.bot.delete_message(chat_id=query.from_user.id, message_id=suggestion.mess_id)

    await query.answer(text=TEXT_MESSAGES['posted'], show_alert=True)
    await query.message.delete()






@main_menu_router.callback_query(MenuCallBack.filter(F.data == "reject"))
async def reject_callback(query: CallbackQuery, session: AsyncSession, callback_data: MenuCallBack):
    await query.answer()
    suggestion_id = callback_data.suggestion_id

    # finding record where suggestion.suggestion_id == suggestion_id
    suggestions = await orm_extract_suggestions(session, suggestion_id)
    await query.message.delete()

    if suggestions:
        for suggestion in suggestions:
            try:
                await query.bot.delete_message(query.message.chat.id, suggestion.mess_id)
            except Exception as e:
                logging.error("The message in the admin chat could not be deleted. Incorrect suggestion_id passed",
                              exc_info=e)
    else:
        logging.error("No suggestions found.")



@main_menu_router.callback_query(MenuCallBack.filter(F.data == "ban"))
async def ban_callback(query: CallbackQuery, session: AsyncSession, callback_data: MenuCallBack):
    suggestion_id = callback_data.suggestion_id

    if await orm_block_user_by_sug_id(session, suggestion_id):
        text = TEXT_MESSAGES['has_banned']
    else:
        text = TEXT_MESSAGES['failed_ban']
        logging.error("Ban failed")

    await query.answer(text=text, show_alert=True)

@main_menu_router.callback_query(MenuCallBack.filter(F.data == "edit"))
async def show_edit_menu(query: CallbackQuery, callback_data: MenuCallBack):
    user_id = callback_data.user_id
    suggestion_id = callback_data.suggestion_id

    await query.message.edit_reply_markup(reply_markup=create_edit_menu_keyboard(user_id, suggestion_id))

    await query.answer()





########################################################

@main_menu_router.callback_query(MenuCallBack.filter(F.data == "edit_text"))
async def request_for_edit_text(query: CallbackQuery, callback_data: MenuCallBack, state: FSMContext):

    await state.update_data(suggestion_id=callback_data.suggestion_id)
    await state.set_state(EditMessage.edit_text)
    await query.answer(text=TEXT_MESSAGES['edit_text'], show_alert=True)


@main_menu_router.message(EditMessage.edit_text)
async def edit_text_message(message: Message, session: AsyncSession, state: FSMContext):
    text = message.text
    entities = message.entities
    data = await state.get_data()
    suggestion_id = data['suggestion_id']

    suggestions = await orm_get_suggestions(session, suggestion_id)

    # If suggestion is an album
    if len(suggestions) > 1:
        try:
            if await message.bot.edit_message_caption(chat_id=message.chat.id,
                                                      message_id=suggestions[0].mess_id,
                                                      caption=text,
                                                      caption_entities=entities
                                                      ):
                if not await orm_update_caption(session,
                                                suggestions[0].suggestion_id,
                                                caption=text,
                                                caption_entities=entities):
                    await message.answer(text="The message could not be edited.", show_alert=True)
        except Exception as e:
            logging.error("The message in the admin chat could not be edited.", exc_info=e)

    # If suggestion is one message with photo or text only
    elif len(suggestions) == 1:
        try:
            await message.bot.edit_message_text(chat_id=message.chat.id,
                                                message_id=suggestions[0].mess_id,
                                                text=text,
                                                entities=entities)
        except:
            logging.error("The message in the admin chat could not be edited.")
        try:
            await message.bot.edit_message_caption(chat_id=message.chat.id,
                                                   message_id=suggestions[0].mess_id,
                                                   caption=text,
                                                   caption_entities=entities)
        except:
            logging.error("The message in the admin chat could not be edited.")

    await state.clear()
    await message.delete()


@main_menu_router.callback_query(MenuCallBack.filter(F.data == "back"))
async def back_to_main_menu(query: CallbackQuery, callback_data: MenuCallBack, state: FSMContext):
    user_id = callback_data.user_id
    suggestion_id = callback_data.suggestion_id

    await query.message.edit_reply_markup(reply_markup=create_main_menu_keyboard(user_id=user_id,
                                                                                 suggestion_id=suggestion_id))

    await state.clear()
    await query.answer()


@main_menu_router.message()
async def echo(message: Message):
    await message.delete()
    await message.answer(TEXT_MESSAGES['echo'], reply_markup=create_ok_menu())

