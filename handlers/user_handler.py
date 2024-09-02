import logging

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InputMediaPhoto, MessageEntity
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from sqlalchemy.ext.asyncio import AsyncSession

from config import TEXT_MESSAGES, ADMIN_USER_ID, LINK, LINK_TEXT

from database.orm_query import orm_add_user, orm_add_new_suggestion, orm_add_new_suggestions, \
    orm_add_help_mess_id_for_suggestion

from keyboards.inline import create_main_menu_keyboard
from scripts.clear_db_admin_chat import schedule_message_deletion

user_router = Router()
flags = {"throttling_key": "default"}


async def send_inline_keyboard(message: Message, suggestion_id: int):
    """A common function for handlers. Creates help message with inline keyboard. Returns its id"""
    return await message.bot.send_message(chat_id=ADMIN_USER_ID,
                                          text=TEXT_MESSAGES['choose'],
                                          reply_markup=create_main_menu_keyboard(message.from_user.id, suggestion_id))


@user_router.message(CommandStart())
async def user_start(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    try:
        await orm_add_user(session, user_id)
    except Exception as e:
        logging.exception("The user entered /start again", exc_info=e)

    await message.reply(TEXT_MESSAGES['start'])


@user_router.message(F.media_group_id, flags=flags)
async def handle_photo_albums(message: Message, session: AsyncSession, scheduler: AsyncIOScheduler, album: list = None):
    """A handler for working with photo albums sent by the user."""

    # Limit on the number of messages in an album
    if len(album) > 3:
        await message.reply(TEXT_MESSAGES['album_limit'])
        return

    user_id = message.from_user.id
    caption = album[0].caption if album[0].caption else ""

    # Adding the link text to the end
    caption += f"\n\n{LINK_TEXT}"

    # Creating a new entity for the link
    if album[0].caption_entities:
        caption_entities = list(album[0].caption_entities)
    else:
        caption_entities = []

    # Adding entity of link to the caption_entities
    start_index = len(caption) - len(LINK_TEXT)
    link_entity = MessageEntity(type="text_link", offset=start_index, length=len(LINK_TEXT), url=LINK)
    caption_entities.append(link_entity)

    # Creating a list of media to send the album, adding a caption only to the first photo
    media_group = [InputMediaPhoto(media=media.photo[-1].file_id,
                                   caption=caption if idx == 0 else '',
                                   caption_entities=caption_entities if idx == 0 else None)
                   for idx, media in enumerate(album)]

    # Sending the media group to the administrator and get a list of new messages to receive IDs
    new_messages = await message.bot.send_media_group(ADMIN_USER_ID, media_group)
    mess_ids = [mess_id.message_id for mess_id in new_messages]

    # Getting ids of files
    file_ids = []
    for idx, media in enumerate(album):
        file_ids.append(media.photo[-1].file_id)

    # Zipping ids for saving in db
    file_ids_with_mess_ids = zip(mess_ids, file_ids)

    try:
        suggestion_id = await orm_add_new_suggestions(session,
                                                      user_id,
                                                      file_ids_with_mess_ids=file_ids_with_mess_ids,
                                                      caption=caption,
                                                      entities=caption_entities)
        # Plan to delete the message in 47 hours
        await schedule_message_deletion(
            bot=message.bot,
            session=session,
            message_ids=mess_ids,
            suggestion_id=suggestion_id,
            scheduler=scheduler
        )
        help_message = await send_inline_keyboard(message, suggestion_id)
        await orm_add_help_mess_id_for_suggestion(session, suggestion_id, help_message.message_id)

    except Exception as e:
        logging.exception("The suggestion could not be written to the database", exc_info=e)

    await message.reply(TEXT_MESSAGES['pending'])


@user_router.message(F.photo, flags=flags)
async def handle_message_with_photo(message: Message, session: AsyncSession, scheduler: AsyncIOScheduler):
    user_id = message.from_user.id

    # Set caption
    caption = message.caption if message.caption else ""
    # Adding the link text to the end
    caption += f"\n\n{LINK_TEXT}"

    # Set entities
    if message.caption_entities:
        caption_entities = list(message.caption_entities)
    else:
        caption_entities = []
    start_index = len(caption) - len(LINK_TEXT)
    link_entity = MessageEntity(type="text_link", offset=start_index, length=len(LINK_TEXT), url=LINK)
    caption_entities.append(link_entity)

    # Send new message
    new_message = await message.bot.send_photo(
        chat_id=ADMIN_USER_ID,
        photo=message.photo[-1].file_id,
        caption=caption,
        caption_entities=caption_entities
    )

    try:
        suggestion_id = await orm_add_new_suggestion(session, user_id, new_message.message_id)

        # Plan to delete the message in 47 hours
        await schedule_message_deletion(
            bot=message.bot,
            session=session,
            message_ids=[new_message.message_id],
            suggestion_id=suggestion_id,
            scheduler=scheduler
        )

        help_message = await send_inline_keyboard(message, suggestion_id)
        await orm_add_help_mess_id_for_suggestion(session, suggestion_id, help_message.message_id)

    except Exception as e:
        logging.exception("The suggestion could not be written to the database", exc_info=e)

    await message.reply(TEXT_MESSAGES['pending'])


@user_router.message(F.text, flags=flags)
async def handle_message_with_text(message: Message, session: AsyncSession, scheduler: AsyncIOScheduler):
    user_id = message.from_user.id

    # Set text
    message_text = message.text if message.text else ""
    # Adding the link text to the end
    message_text += f"\n\n{LINK_TEXT}"

    # Set entities
    if message.entities:
        entities = list(message.entities)
    else:
        entities = []
    start_index = len(message_text) - len(LINK_TEXT)
    link_entity = MessageEntity(type="text_link", offset=start_index, length=len(LINK_TEXT), url=LINK)
    entities.append(link_entity)

    # Send new message
    new_message = await message.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=message_text,
        entities=entities
    )

    try:
        suggestion_id = await orm_add_new_suggestion(session, user_id, new_message.message_id)

        # Plan to delete the message in 47 hours
        await schedule_message_deletion(
            bot=message.bot,
            session=session,
            message_ids=[new_message.message_id],
            suggestion_id=suggestion_id,
            scheduler=scheduler
        )

        help_message = await send_inline_keyboard(message, suggestion_id)
        await orm_add_help_mess_id_for_suggestion(session, suggestion_id, help_message.message_id)
    except Exception as e:
        logging.exception("The suggestion could not be written to the database", exc_info=e)

    await message.reply(TEXT_MESSAGES['pending'])


@user_router.message(F.sticker | F.gif | F.video | F.voice | F.document)
async def handle_sticker_message(message: Message):
    await message.reply(TEXT_MESSAGES['unsupported_format'])


@user_router.message()
async def echo(message: Message):
    await message.answer(TEXT_MESSAGES['echo'])