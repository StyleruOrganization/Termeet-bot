from typing import TYPE_CHECKING

from aiogram import Router


if TYPE_CHECKING:
    from aiogram import Bot

router = Router()


async def handler_order(data: dict, bot: "Bot"):
    print(f"Received message {data}")
    text = f"Received message {data}"
    chat_id: int = 5030074090
    await bot.send_message(chat_id=chat_id, text=text)
