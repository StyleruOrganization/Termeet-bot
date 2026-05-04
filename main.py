import asyncio
import logging
from contextlib import asynccontextmanager
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse

from config import settings, logger
from handlers import user_router, webhook_router
from middlewares import LoggingMiddleware

# Initialize bot and dispatcher
bot = Bot(
    token=settings.TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()
dp.include_routers(user_router, webhook_router)
dp.message.middleware(LoggingMiddleware())

# Store bot instance for webhook handlers
_bot_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    global _bot_instance
    _bot_instance = bot
    
    logger.info("Bot started")
    yield
    
    logger.info("Bot stopped")
    await bot.session.close()


# Create FastAPI app for webhook support
app = FastAPI(title="Termeet Bot API", lifespan=lifespan)


@app.post("/webhook/meeting_created")
async def webhook_meeting_created(
    request: Request,
    x_webhook_token: str = Header(None)
) -> dict:
    """
    Webhook endpoint for receiving notifications about created meetings.
    
    Expected payload:
    {
        "meeting_id": "abc123",
        "created_by_chat_id": 123456789,
        "meeting_link": "https://teermet.tech/meet?id=abc123",
        "title": "Team Standup"
    }
    """
    # Verify webhook token
    if x_webhook_token != settings.WEBHOOK_SECRET_TOKEN:
        logger.warning("Webhook called with invalid token")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        payload = await request.json()
        logger.info(f"Webhook received: {payload}")
        
        chat_id = payload.get("created_by_chat_id")
        meeting_id = payload.get("meeting_id")
        meeting_link = payload.get("meeting_link")
        title = payload.get("title", "Новая встреча")
        
        if not all([chat_id, meeting_id, meeting_link]):
            logger.error("Invalid webhook payload")
            return {"status": "error", "message": "Invalid payload"}
        
        # Send notification to chat
        notification_text = (
            f"📅 <b>{title}</b>\n\n"
            f"✅ Встреча создана!\n\n"
            f"🔗 <a href='{meeting_link}'>Проголосуйте за время встречи</a>"
        )
        
        await bot.send_message(
            chat_id=chat_id,
            text=notification_text,
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"Notification sent to chat {chat_id} for meeting {meeting_id}")
        
        return {"status": "success", "meeting_id": meeting_id}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "bot": "running"}


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": "Termeet Telegram Bot",
        "version": "1.0.0",
        "status": "running"
    }


async def main_polling():
    """Run bot with polling (for development)."""
    logger.info("Starting bot in polling mode...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def main_webhook():
    """
    Run bot with webhook (for production).
    Note: Requires external HTTPS server proxy.
    """
    logger.info("Starting bot in webhook mode...")
    
    # This is a simplified example. In production, you'd use:
    # - nginx/Apache as reverse proxy
    # - SSL certificate
    # - Proper error handling
    
    import uvicorn
    
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    finally:
        await bot.session.close()


if __name__ == "__main__":
    # For dev
    asyncio.run(main_polling())
    
    # For prod
    # asyncio.run(main_webhook())
