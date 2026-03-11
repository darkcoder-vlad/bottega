from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable, Union
from database.database import get_session


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to provide database session"""
    
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        db = get_session()
        try:
            data['db'] = db
            return await handler(event, data)
        finally:
            db.close()
