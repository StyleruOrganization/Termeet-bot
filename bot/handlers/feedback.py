from typing import TYPE_CHECKING
import time

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state

from bot.config import config
from bot.api.termeet import termeet_client
from bot.metrics import get_feedback_latency

if TYPE_CHECKING:
    from aiogram import Bot
    from bot.api.schemas import Feedback

router = Router()


async def handler_order(data: dict, bot: "Bot"):
    text = (
        f"💥Получен отзыв от {data['contact']}💥\n"
        f"Чтобы посмотреть используйте команду /feedback_json или /feedback_grpc"
    )
    for chat_id in config.telegram.CHAT_IDS_FOR_FEEDBACK:
        await bot.send_message(chat_id=chat_id, text=text)


@router.message(Command("feedback_json"), StateFilter(default_state))
async def get_all_feedback_json(message: Message):

    try:
        start = time.perf_counter()
        feedbacks: list[Feedback] = (
            await termeet_client.get_all_feedback_json()
        )
        end = time.perf_counter()

        get_feedback_latency.labels("json").observe(end - start)

    except Exception:
        await message.answer(
            "Произошла ошибка при получении отзывов. Обратитесь к @d10110101 за помощью"
        )

    lines = []

    for f in feedbacks:
        lines.append(
            f"📩 <b>{f.type.name}</b> | {f.communication_channel.name}: {f.contact}\n"
            f"{f.message}"
        )

    await message.answer("\n".join(lines))


@router.message(Command("feedback_grpc"), StateFilter(default_state))
async def get_all_feedback_grpc(message: Message):

    try:
        start = time.perf_counter()
        feedbacks: list[Feedback] = (
            await termeet_client.get_all_feedback_grpc()
        )
        end = time.perf_counter()

        get_feedback_latency.labels("grpc").observe(end - start)

    except Exception:
        await message.answer(
            "Произошла ошибка при получении отзывов. Обратитесь к @d10110101 за помощью"
        )

    lines = []

    for f in feedbacks:
        lines.append(
            f"📩 <b>{f.type.name}</b> | {f.communication_channel.name}: {f.contact}\n"
            f"{f.message}"
        )

    await message.answer("\n".join(lines))
