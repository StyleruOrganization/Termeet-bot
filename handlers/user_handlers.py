"""User command handlers for Termeet Bot."""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from services.meeting_service import MeetingService
from utils.keyboards import get_inline_keyboard

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
        reply_markup=get_inline_keyboard()
    )


@router.message(Command("meeting"))
async def meeting_command(message: Message) -> None:
    """Handle /meeting command - create new meeting."""
    logger.info(f"User {message.from_user.id} requested to create meeting")
    
    meeting_url = meeting_service.generate_meeting_url()
    
    meeting_text = (
        "Создайте новую встречу\n\n"
        "Нажимайте на кнопку ниже, чтобы перейти на сайт и создать встречу:"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Перейти к встрече",
                url=meeting_url
            )]
        ]
    )
    
    await message.answer(meeting_text, reply_markup=keyboard)


# Callback handler for "create_meeting" button
@router.callback_query(F.data == "create_meeting")
async def create_meeting_callback(callback: CallbackQuery) -> None:
    """Handle 'create_meeting' callback from inline button."""
    logger.info(f"User {callback.from_user.id} clicked create meeting button")
    
    meeting_url = meeting_service.generate_meeting_url()
    
    meeting_text = (
        "Создайте новую встречу\n\n"
        "Нажимайте на кнопку ниже, чтобы перейти на сайт и создать встречу:"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Перейти к встрече",
                url=meeting_url
            )]
        ]
    )
    
    await callback.message.edit_text(meeting_text, reply_markup=keyboard)
    await callback.answer()
@router.message(Command("help"))
async def help_command(message: Message) -> None:
    """Handle /help command - show available commands."""
    logger.info(f"User {message.from_user.id} requested help")
    
    help_text = (
        "<b>Доступные команды:</b>\n\n"
        "/start - Приветствие и информация о боте\n"
        "/meeting - Создать новую встречу\n"
        "/help - Показать эту справку\n\n"
        "<b>Как это работает:</b>\n"
        "1️⃣ Нажмите /meeting или используйте кнопку\n"
        "2️⃣ Перейдите по ссылке и создайте встречу\n"
        "3️⃣ Выберите временной промежуток\n"
        "4️⃣ Пригласите друзей проголосовать\n"
        "5️⃣ После создания встречи вы получите уведомление в этом чате"
    )
    
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_inline_keyboard())


@router.callback_query(F.data == "show_help")
async def show_help_callback(callback: CallbackQuery) -> None:
    """Handle 'show_help' callback from inline button."""
    logger.info(f"User {callback.from_user.id} clicked help button")
    
    help_text = (
        "<b>Доступные команды:</b>\n\n"
        "/start - Приветствие и информация о боте\n"
        "/meeting - Создать новую встречу\n"
        "/help - Показать эту справку\n\n"
        "<b>Как это работает:</b>\n"
        "1️⃣ Нажмите /meeting или используйте кнопку\n"
        "2️⃣ Перейдите по ссылке и создайте встречу\n"
        "3️⃣ Выберите временной промежуток\n"
        "4️⃣ Пригласите друзей проголосовать\n"
        "5️⃣ После создания встречи вы получите уведомление в этом чате"
    )
    
    await callback.message.edit_text(help_text, parse_mode="HTML", reply_markup=get_inline_keyboard())
    await callback.answer()


@router.message(Command("about"))
async def about_command(message: Message) -> None:
    """Handle /about command."""
    logger.info(f"User {message.from_user.id} requested about info")
    
    about_text = (
        "<b>О боте Termeet</b>\n\n"
        "Termeet Bot помогает организовывать встречи в команде.\n\n"
        "<b>Основные функции:</b>\n"
        "• Создание встреч с указанием временных промежутков\n"
        "• Голосование участников за удобное время\n"
        "• Уведомления в Telegram\n\n"
        "<b>Версия:</b> 1.0.0\n"
        "<b>Разработчик:</b> Termeet Team\n\n"
        "Для помощи используйте /help"
    )
    
    await message.answer(about_text, parse_mode="HTML", reply_markup=get_inline_keyboard())


@router.callback_query(F.data == "show_about")
async def show_about_callback(callback: CallbackQuery) -> None:
    """Handle 'show_about' callback from inline button (edit message)."""
    logger.info(f"User {callback.from_user.id} clicked about button")
    
    about_text = (
        "<b>О боте Termeet</b>\n\n"
        "Termeet Bot помогает организовывать встречи в команде.\n\n"
        "<b>Основные функции:</b>\n"
        "• Создание встреч с указанием временных промежутков\n"
        "• Голосование участников за удобное время\n"
        "• Уведомления в Telegram\n\n"
        "<b>Версия:</b> 1.0.0\n"
        "<b>Разработчик:</b> Termeet Team\n\n"
        "Для помощи используйте /help"
    )
    
    await callback.message.edit_text(about_text, parse_mode="HTML", reply_markup=get_inline_keyboard())
    await callback.answer()


@router.message()
async def echo_handler(message: Message) -> None:
    """Handle unknown messages."""
    logger.info(f"User {message.from_user.id} sent unknown message: {message.text}")
    
    text = (
        "🤔 Я не понимаю эту команду.\n\n"
        "Используйте /help для списка доступных команд."
    )
    
    await message.answer(text)
