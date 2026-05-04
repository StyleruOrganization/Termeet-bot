"""Keyboard layouts for Termeet Bot."""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Get main reply keyboard.
    
    Returns:
        ReplyKeyboardMarkup with main commands
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Создать встречу"),
                KeyboardButton(text="Помощь")
            ],
            [
                KeyboardButton(text="О боте")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard
