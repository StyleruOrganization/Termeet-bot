from typing import TYPE_CHECKING
import json
import asyncio
from collections.abc import Callable, Awaitable

import aio_pika

if TYPE_CHECKING:
    from aiogram import Bot

MessageHandler = Callable[[dict], Awaitable[None]]


class RabbitMQClient:
    def __init__(self, url: str, handler: MessageHandler, bot: "Bot"):
        self.url: str = url
        self._handler = handler
        self._bot = bot
        self._task: asyncio.Task | None = None

    async def _handle(self, message: aio_pika.abc.AbstractIncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body)
                await self._handler(data, self._bot)
            except json.JSONDecodeError:
                raise
            except Exception:
                raise

    async def _consume_loop(self):
        while True:
            try:
                connection = await aio_pika.connect_robust(self.url)
                async with connection:
                    channel = await connection.channel()
                    await channel.set_qos(prefetch_count=1)
                    queue = await channel.declare_queue(
                        "feedback_queue", durable=True
                    )

                    async with queue.iterator() as queue_iter:
                        async for message in queue_iter:
                            await self._handle(message)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)

    def start(self):
        self._task = asyncio.create_task(self._consume_loop())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
