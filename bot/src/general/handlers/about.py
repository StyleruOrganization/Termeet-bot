from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state

from bot.src.config import config

router = Router()


@router.message(Command("about"), StateFilter(default_state))
async def about_handler(message: Message):
    await message.answer(
        "🤖 <b>Termeet Bot</b>\n\n"
        "AI-операционная система для командных встреч в Telegram.\n"
        "Помогает координировать встречи от планирования до распределения задач.\n"
        f"\nСайт: {config.telegram.TERMEET_DOMAIN}"
    )
