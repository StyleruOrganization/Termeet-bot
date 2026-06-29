import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from prometheus_client import start_http_server

from bot.src.config import config
from bot.src.general.set_menu import set_main_menu
from bot.src.general.handlers.start import router as start_router
from bot.src.general.handlers.about import router as about_router
from bot.src.meetings.handlers import router as create_router
from bot.src.feedback.handlers import handler_order
from bot.src.broker import RabbitMQClient


bot = Bot(
    token=config.telegram.TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()

dp.include_routers(
    start_router,
    about_router,
    create_router,
)

consumer = RabbitMQClient(
    url=config.rabbitmq.rb_url, handler=handler_order, bot=bot
)


@dp.startup()
async def on_startup():
    consumer.start()


async def main_polling():
    await set_main_menu(bot)

    start_http_server(9090)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main_polling())
