from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable, Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware to log all events"""
    
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            logger.info(
                f"Message from @{event.from_user.username or event.from_user.first_name} "
                f"(ID: {event.from_user.id}): {event.text or 'Media/Sticker'}"
            )
        elif isinstance(event, CallbackQuery):
            logger.info(
                f"Callback from @{event.from_user.username or event.from_user.first_name} "
                f"(ID: {event.from_user.id}): {event.data}"
            )
        
        return await handler(event, data)
