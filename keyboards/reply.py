from aiogram.types import KeyboardButton
from config import TEXT_MESSAGES
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def admin_reply_keyboard():
    builder = ReplyKeyboardBuilder()

    builder.row(KeyboardButton(text=TEXT_MESSAGES['rm']))

    builder.row(KeyboardButton(text=TEXT_MESSAGES['banlist']))

    return builder.as_markup(resize_keyboard=True)
