"""Keyboard layouts for Termeet Bot."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard() -> InlineKeyboardMarkup:
    """
    Get main inline keyboard.
    
    Returns:
        InlineKeyboardMarkup with main command buttons
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Создать встречу",
                    callback_data="create_meeting"
                ),
                InlineKeyboardButton(
                    text="Помощь",
                    callback_data="show_help"
                )
            ],
            [
                InlineKeyboardButton(
                    text="О боте",
                    callback_data="show_about"
                )
            ]
        ]
    )
    return keyboard
