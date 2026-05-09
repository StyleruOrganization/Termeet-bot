"""Callback helpers for Termeet Bot."""

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from .keyboards import get_inline_keyboard


async def edit_callback_message_if_needed(callback: CallbackQuery, text: str) -> None:
    """Answer a callback and edit the message only when the text changes."""
    await callback.answer()

    if callback.message is None:
        return

    current_text = callback.message.text or ""
    if current_text == text:
        return

    try:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_inline_keyboard(),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc).lower():
            return
        raise