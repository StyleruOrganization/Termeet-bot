"""Logging middleware for all updates."""

import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Update

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging all incoming updates."""
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        """Log update and pass to handler."""
        
        if event.message:
            logger.info(
                f"Incoming message from {event.message.from_user.id}: {event.message.text}"
            )
        elif event.callback_query:
            logger.info(
                f"Callback query from {event.callback_query.from_user.id}: {event.callback_query.data}"
            )
        else:
            logger.debug(f"Update: {event.update_id}")
        
        return await handler(event, data)
