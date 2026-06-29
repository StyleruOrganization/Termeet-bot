from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
import aioboto3

from bot.src.config import config
from bot.src.meetings.api import termeet_client

if TYPE_CHECKING:
    from aiogram import Bot
    from bot.src.meetings.schemas import Feedback

router = Router()


async def handler_order(data: dict, bot: "Bot"):
    if data['communication_channel'] == "TELEGRAM" and data['contact'][0] != "@":
        data['contact'] = f"@{data['contact']}"
    text = (
        f"💥Получен отзыв {data['type']} от\n"
        f"{data['communication_channel']} {data['contact']}:\n"
        f"`{data['message']}`"
    )

    if data['count_photos'] != 0:
        session = aioboto3.Session()

        try:
            async with session.client(
                "s3",
                aws_access_key_id=config.s3.ACCESS_KEY,
                aws_secret_access_key=config.s3.SECRET_KEY,
                endpoint_url=config.s3.ENDPOINT,
            ) as client:
                images: list[BufferedInputFile] = []
                for i in range(data['count_photos']):
                    s3_object = await client.get_object(Bucket=config.s3.BUCKET_NAME, Key=f"{data['id']}/{data['id']}_{i}.jpg")
                    photo_bytes = await s3_object["Body"].read()
                    images.append(BufferedInputFile(photo_bytes, filename=f"Фото {i+1} от {data['contact']}"))

        except Exception as e:
            print(f"!!!Error: {e}", flush=True)

    for i in range(0, len(config.telegram.CHAT_IDS_FOR_FEEDBACK)):
        chat_id = config.telegram.CHAT_IDS_FOR_FEEDBACK[i]
        message_thread_id = (
            config.telegram.THREAD_IDS_FOR_FEEDBACK[i]
            if config.telegram.THREAD_IDS_FOR_FEEDBACK[i] != 0
            else None
        )
        await bot.send_message(
            chat_id=chat_id, text=text, message_thread_id=message_thread_id
        )
        for image in images:
            await bot.send_photo(chat_id=chat_id, photo=image, message_thread_id=message_thread_id)


@router.message(Command("feedback_json"), StateFilter(default_state))
async def get_all_feedback_json(message: Message):

    try:
        feedbacks: list[Feedback] = (
            await termeet_client.get_all_feedback_json()
        )

    except Exception:
        await message.answer(
            "❌ Ошибка при получении отзывов. Обратитесь к @d10110101 за помощью"
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
        feedbacks: list[Feedback] = (
            await termeet_client.get_all_feedback_grpc()
        )

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
