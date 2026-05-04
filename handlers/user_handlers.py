"""User command handlers for Termeet Bot."""

import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import settings
from services.meeting_service import MeetingService
from utils.keyboards import get_main_keyboard

logger = logging.getLogger(__name__)
router = Router()

meeting_service = MeetingService()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """Handle /start command."""
    logger.info(f"User {message.from_user.id} started bot")
    
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я помогу вам организовать встречу в команде! \n\n"
        "С помощью меня вы можете:\n"
        "• Создавать встречи для своей команды\n"
        "• Отправлять ссылки на голосование за время встречи\n"
        "• Получать уведомления когда встреча создана\n\n"
        "Используйте команду /meeting для начала 👇"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard()
    )


@router.message(Command("meeting"))
async def meeting_handler(message: Message) -> None:
    """Handle /meeting command - create new meeting."""
    logger.info(f"User {message.from_user.id} requested to create meeting")
    
    meeting_url = meeting_service.generate_meeting_url()
    
    meeting_text = (
        " Создайте новую встречу\n\n"
        "Нажимайте на кнопку ниже, чтобы перейти на сайт и создать встречу:"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Создать встречу",
                url=meeting_url
            )]
        ]
    )
    
    await message.answer(meeting_text, reply_markup=keyboard)


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    """Handle /help command - show available commands."""
    logger.info(f"User {message.from_user.id} requested help")
    
    help_text = (
        "ℹ️ <b>Доступные команды:</b>\n\n"
        "/start - Приветствие и информация о боте\n"
        "/meeting - Создать новую встречу\n"
        "/help - Показать эту справку\n\n"
        "<b>Как это работает:</b>\n"
        "1️⃣ Нажмите /meeting\n"
        "2️⃣ Перейдите по ссылке и создайте встречу\n"
        "3️⃣ Выберите временной промежуток\n"
        "4️⃣ Пригласите друзей проголосовать\n"
        "5️⃣ После создания встречи вы получите уведомление в этом чате"
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.message()
async def echo_handler(message: Message) -> None:
    """Handle unknown messages."""
    logger.info(f"User {message.from_user.id} sent unknown message: {message.text}")
    
    text = (
        "Я не понимаю эту команду.\n\n"
        "Используйте /help для списка доступных команд."
    )
    
    await message.answer(text)
