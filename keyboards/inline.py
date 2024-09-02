from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData



class MenuCallBack(CallbackData, prefix="menu"):
    suggestion_id: int
    user_id: int | None = None
    data: str


def create_main_menu_keyboard(user_id, suggestion_id):
    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="✅ Post",
        callback_data=MenuCallBack(suggestion_id=suggestion_id, data="post")
    )
    keyboard.button(
        text="📋 Edit",
        callback_data=MenuCallBack(user_id=user_id, suggestion_id=suggestion_id, data="edit")
    )
    keyboard.button(
        text="🙅‍♂️ Reject",
        callback_data=MenuCallBack(suggestion_id=suggestion_id, data="reject")
    )
    keyboard.button(
        text="❌ Ban",
        callback_data=MenuCallBack(suggestion_id=suggestion_id, data="ban")
    )
    keyboard.button(
        text="👤 Profile",
        url=f"tg://user?id={user_id}"
    )

    return keyboard.as_markup()


def create_edit_menu_keyboard(user_id, suggestion_id):
    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="Edit Text",
        callback_data=MenuCallBack(suggestion_id=suggestion_id, data="edit_text")
    )
    # keyboard.button(
    #     text="Edit Photo",
    #     callback_data="edit_photo"
    # )
    keyboard.button(
        text="Back",
        callback_data=MenuCallBack(user_id=user_id, suggestion_id= suggestion_id, data="back")
    )

    return keyboard.as_markup()


def create_ok_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='✅OK',
                callback_data="delete_mes"
            )]
        ]
    )
    return keyboard