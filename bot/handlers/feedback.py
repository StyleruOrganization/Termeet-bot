from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state

from bot.config import config
from bot.api.termeet import termeet_client


if TYPE_CHECKING:
    from aiogram import Bot

router = Router()


async def handler_order(data: dict, bot: "Bot"):
    text = (
        f"💥Получен отзыв от {data["contact"]}💥\n"
        f"Чтобы посмотреть используйте команду /feedback"
    )
    chat_id = config.telegram.CHAT_ID_FOR_FEEDBACK
    await bot.send_message(chat_id=chat_id, text=text)


@router.message(Command("feedback"), StateFilter(default_state))
async def get_all_feedback(message: Message):
    feedbacks = await termeet_client.get_all_feedback()
    if not feedbacks:
        await message.answer("Отзывов пока нет.")
        return
    lines = []
    for f in feedbacks:
        lines.append(
            f"📩 <b>{f['type']}</b> | {f['communication_channel']}: {f['contact']}\n"
            f"{f['message']}"
        )
    await message.answer("Все отзывы:\n\n" + "\n\n".join(lines))
