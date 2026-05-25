from aiogram import Router
from aiogram.types import Message

from bot.database import queries as db

router = Router()


@router.message()
async def track_member(message: Message):
    """Silently record every sender in group chats to build the known-members list."""
    if message.chat.type not in ("group", "supergroup"):
        return
    user = message.from_user
    if not user or user.is_bot:
        return
    await db.upsert_chat_member(
        chat_id=message.chat.id,
        tg_user_id=user.id,
        first_name=user.first_name,
        username=user.username,
        last_name=user.last_name,
    )
