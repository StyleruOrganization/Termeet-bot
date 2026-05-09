"""Logging middleware for all updates."""

import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging all incoming messages."""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        """Log message and pass to handler."""
        
        user_id = event.from_user.id if event.from_user else "Unknown"
        text = event.text or "(no text)"
        
        logger.info(
            f"Incoming message from {user_id}: {text}"
        )
        
        return await handler(event, data)
