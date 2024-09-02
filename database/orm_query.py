import logging
import json

from aiogram.types import MessageEntity
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Suggestion


def serialize_entities(entities: list[MessageEntity]) -> list[dict]:
    return [
        {
            "type": entity.type,
            "offset": entity.offset,
            "length": entity.length,
            "url": entity.url,
            "user": entity.user.id if entity.user else None,
            "language": entity.language,
            "custom_emoji_id": entity.custom_emoji_id,
        }
        for entity in entities
    ]


def deserialize_entities(entities_data: list[dict]) -> list[MessageEntity]:
    return [
        MessageEntity(
            type=entity["type"],
            offset=entity["offset"],
            length=entity["length"],
            url=entity.get("url"),
            user=entity.get("user"),
            language=entity.get("language"),
            custom_emoji_id=entity.get("custom_emoji_id"),
        )
        for entity in entities_data
    ]


async def orm_add_user(session: AsyncSession, user_id: int):
    user = User(
        user_id=user_id
    )

    session.add(user)
    await session.commit()


async def orm_get_user(session: AsyncSession, user_id: int):
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()


async def get_next_suggestion_id(session: AsyncSession) -> int:
    result = await session.execute(select(func.max(Suggestion.suggestion_id)))
    max_suggestion_id = result.scalar_one_or_none()
    return (max_suggestion_id or 0) + 1


async def orm_add_new_suggestion(session: AsyncSession, user_id: int, new_mess_id: int):
    next_suggestion_id = await get_next_suggestion_id(session)

    suggestion = Suggestion(user_id=user_id,
                            mess_id=new_mess_id,
                            suggestion_id=next_suggestion_id)
    session.add(suggestion)
    await session.commit()
    return next_suggestion_id


async def orm_add_new_suggestions(session: AsyncSession, user_id: int, file_ids_with_mess_ids: dict[int, str],
                                  caption: str, entities: list[MessageEntity]):
    next_suggestion_id = await get_next_suggestion_id(session)
    serialized_entities = serialize_entities(entities)

    suggestions = [
        Suggestion(user_id=user_id,
                   mess_id=new_mess_id,
                   suggestion_id=next_suggestion_id,
                   file_id=file_id
                   )
        for new_mess_id, file_id in file_ids_with_mess_ids
    ]
    suggestions[0].caption = caption  # set caption only for first record in db
    suggestions[0].entities = serialized_entities

    session.add_all(suggestions)
    await session.commit()
    return next_suggestion_id


async def orm_get_and_delete_all_suggestions(session: AsyncSession) -> list[Suggestion]:
    query = select(Suggestion)
    result = await session.execute(query)
    suggestions = result.scalars().all()

    delete_query = delete(Suggestion)
    await session.execute(delete_query)
    await session.commit()

    return suggestions


async def orm_get_banned_users(session: AsyncSession):
    query = select(User).where(User.is_banned == True)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_block_user_by_sug_id(session: AsyncSession, suggestion_id: int):
    query = select(Suggestion).where(Suggestion.suggestion_id == suggestion_id)
    result = await session.execute(query)
    suggestion = result.scalars().first()

    if not suggestion:
        return False

    user_id_to_ban = suggestion.user_id

    query = update(User).where(User.user_id == user_id_to_ban, User.is_banned == False).values(
        is_banned=True)
    result = await session.execute(query)
    await session.commit()

    if result.rowcount == 0:
        return False

    return True


async def orm_unblock_user(session: AsyncSession, user_id: int) -> bool:
    query = update(User).where(User.user_id == user_id, User.is_banned == True).values(
        is_banned=False)  #.execution_options(synchronize_session="fetch")

    result = await session.execute(query)
    await session.commit()

    if result.rowcount == 0:
        return False

    return True


async def orm_extract_suggestions(session: AsyncSession, suggestion_id: int):
    try:
        # Checking the availability of a suggestion
        query = select(Suggestion).where(Suggestion.suggestion_id == suggestion_id)
        result = await session.execute(query)
        suggestions = result.scalars().all()

        if not suggestions:
            return None

        # Deleting the suggestion
        delete_query = delete(Suggestion).where(Suggestion.suggestion_id == suggestion_id)
        await session.execute(delete_query)
        await session.commit()

        # Deserializing entities
        if suggestions[0].entities:
            suggestions[0].entities = deserialize_entities(suggestions[0].entities)

        return suggestions

    except Exception as e:
        logging.exception(f"An error occurred", exc_info=e)
        return None


async def orm_get_suggestions(session: AsyncSession, suggestion_id: int) -> list[Suggestion]:
    try:
        # Checking the availability of a suggestion
        query = select(Suggestion).where(Suggestion.suggestion_id == suggestion_id)
        result = await session.execute(query)
        suggestions = result.scalars().all()

        if not suggestions:
            return None

        # Deserializing entities
        if suggestions[0].entities:
            suggestions[0].entities = deserialize_entities(suggestions[0].entities)

        return suggestions

    except Exception as e:
        logging.exception(f"An error occurred", exc_info=e)
        return None


async def orm_update_caption(session: AsyncSession,
                             suggestion_id: int,
                             caption: str,
                             caption_entities: list[MessageEntity] | None):
    if caption_entities:
        serialized_entities = serialize_entities(caption_entities)
    else:
        serialized_entities = None
    #entities_json = json.dumps(serialized_entities)

    query = (update(Suggestion)
             .where(Suggestion.suggestion_id == suggestion_id, Suggestion.caption is not None)
             .values(caption=caption, entities=serialized_entities)
             )

    result = await session.execute(query)
    await session.commit()

    if result.rowcount == 0:
        return False

    return True


async def orm_add_help_mess_id_for_suggestion(session: AsyncSession, suggestion_id: int, message_id: int):
    query = update(Suggestion).where(Suggestion.suggestion_id == suggestion_id).values(
        help_message=message_id)

    result = await session.execute(query)
    await session.commit()

    if result.rowcount == 0:
        return False

    return True
