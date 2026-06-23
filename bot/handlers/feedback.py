from typing import TYPE_CHECKING
import time

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
    for chat_id in config.telegram.CHAT_IDS_FOR_FEEDBACK:
        await bot.send_message(chat_id=chat_id, text=text)


@router.message(Command("feedback_json"), StateFilter(default_state))
async def get_all_feedback(message: Message):
    start = time.perf_counter()
    feedbacks = await termeet_client.get_all_feedback_json()
    end = time.perf_counter()
    print(f"Time: {end - start}", flush=True)

    # print(feedbacks, flush=True)

    # if not feedbacks:
    #     await message.answer("Отзывов пока нет.")
    #     return

    # lines = []

    # for f in feedbacks:
    #     lines.append(
    #         f"📩 <b>{f['type']}</b> | {f['communication_channel']}: {f['contact']}\n"
    #         f"{f['message']}"
    #     )

    await message.answer("Ответ получен!")


@router.message(Command("feedback_grpc"), StateFilter(default_state))
async def get_all_feedback_grpc(message: Message):
    start = time.perf_counter()
    feedbacks = await termeet_client.get_all_feedback_grpc()
    end = time.perf_counter()
    print(f"Time: {end - start}", flush=True)
    print(f"Payload: {feedbacks.ByteSize()}", flush=True)

    await message.answer("Ответ получен!")
