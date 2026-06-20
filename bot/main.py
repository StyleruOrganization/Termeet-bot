import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import config
from bot.set_menu import set_main_menu
# from bot.database import init_db
from bot.handlers.start import router as start_router
from bot.handlers.meeting_create import router as create_router
from bot.handlers.meeting_manage import router as manage_router
from bot.handlers.during_meeting import router as during_router
from bot.handlers.member_tracker import router as tracker_router
from bot.handlers.feedback import router as feedback_router, handler_order
from bot.scheduler.setup import scheduler
from bot.scheduler import jobs
from bot.broker import RabbitMQClient

bot = Bot(
    token=config.TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()

dp.include_routers(
    start_router,
    create_router,
    manage_router,
    during_router,
    tracker_router,
    feedback_router,
)


consumer = RabbitMQClient(
    url=config.rabbitmq.rb_url, handler=handler_order, bot=bot
)


@dp.startup()
async def on_startup():
    consumer.start()


async def main_polling():
    # await init_db()
    await set_main_menu(bot)

    # # Smart Nagging: every 4 hours
    # scheduler.add_job(
    #     jobs.check_and_nag,
    #     trigger="interval",
    #     hours=4,
    #     kwargs={"bot": bot},
    #     id="nag",
    #     replace_existing=True,
    # )
    # # Pre-meeting reminders: every 5 minutes
    # scheduler.add_job(
    #     jobs.send_pre_meeting_reminders,
    #     trigger="interval",
    #     minutes=5,
    #     kwargs={"bot": bot},
    #     id="pre_reminder",
    #     replace_existing=True,
    # )
    # # Task follow-ups: daily at 09:00
    # scheduler.add_job(
    #     jobs.send_task_follow_ups,
    #     trigger="cron",
    #     hour=9,
    #     minute=0,
    #     kwargs={"bot": bot},
    #     id="follow_up",
    #     replace_existing=True,
    # )

    scheduler.start()
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main_polling())
