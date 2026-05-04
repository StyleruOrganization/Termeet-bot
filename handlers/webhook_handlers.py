"""Webhook handlers for receiving notifications from backend."""

import logging
from aiogram import Router
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = Router()


class MeetingCreatedWebhook(BaseModel):
    """Schema for meeting created webhook payload."""
    meeting_id: str
    created_by_chat_id: int
    meeting_link: str
    title: str = "Новая встреча"


async def send_meeting_notification(chat_id: int, webhook_data: MeetingCreatedWebhook):
    """
    Send notification about new meeting to chat.
    
    Args:
        chat_id: Telegram chat ID to send notification to
        webhook_data: Meeting data from webhook
    
    Note:
        This function will be called from FastAPI webhook handler.
        Implementation requires passing Bot instance from main.py.
    """
    notification_text = (
        f"📅 <b>{webhook_data.title}</b>\n\n"
        f"Создана новая встреча!\n\n"
        f"🔗 <a href='{webhook_data.meeting_link}'>Проголосуйте за время встречи</a>"
    )
    
    logger.info(f"Meeting {webhook_data.meeting_id} created, preparing notification for chat {chat_id}")
    
    # Note: Bot instance will be injected and called here
    # await bot.send_message(chat_id, notification_text, parse_mode="HTML")
