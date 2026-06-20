from pprint import pprint

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state

router = Router()


@router.message(Command("start"), StateFilter(default_state))
async def start_handler(message: Message):
    name = message.from_user.first_name
    await message.answer(
        f"Привет, {name}! 👋\n\n"
        "Я <b>Termeet Bot</b> — AI-координатор командных встреч.\n\n"
        "<b>До встречи:</b>\n"
        "📅 /meet — создать встречу прямо здесь\n"
        "🔗 /link_meeting — привязать существующую встречу к чату\n"
        "📊 /status — кто уже заполнил слоты\n"
        "✏️ /my_slots — заполнить слоты текстом (AI разберёт)\n\n"
        "<b>Во время встречи:</b>\n"
        "📝 /note — сохранить заметку\n"
        "✅ /task — назначить задачу участнику\n"
        "🏁 /end_meeting — завершить и получить итоги\n\n"
        "Сайт: termeet.tech"
    )
    pprint(message.chat.id)


@router.message(Command("about"), StateFilter(default_state))
async def about_handler(message: Message):
    await message.answer(
        "🤖 <b>Termeet Bot</b>\n\n"
        "AI-операционная система для командных встреч в Telegram.\n"
        "Помогает координировать встречи от планирования до распределения задач.\n\n"
        "termeet.tech"
    )
