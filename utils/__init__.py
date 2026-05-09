"""Utilities package for Termeet Bot."""

from .keyboards import get_input_keyboard, get_inline_keyboard

# Backward-compatible alias for older imports.
get_main_keyboard = get_inline_keyboard

__all__ = ["get_input_keyboard", "get_inline_keyboard", "get_main_keyboard"]
