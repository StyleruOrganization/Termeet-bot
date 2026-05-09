"""Keyboard layouts for Termeet Bot."""

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def get_input_keyboard() -> ReplyKeyboardMarkup:
    """Reply keyboard to send command messages from the input field.

    Note: Telegram buttons in a ReplyKeyboard send their text as a message.
    To trigger command handlers the button text must start with a slash,
    e.g. `/help`.
    """
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="/meeting")],
        [KeyboardButton(text="/help")],
        [KeyboardButton(text="/start")],
    ], resize_keyboard=True)
    return keyboard


def get_inline_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard used under bot messages (uses callback_data)."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Создать встречу",
                    callback_data="create_meeting",
                ),
                InlineKeyboardButton(
                    text="Помощь",
                    callback_data="show_help",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="О боте",
                    callback_data="show_about",
                )
            ],
        ]
    )
    return keyboard
