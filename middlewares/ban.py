from aiogram.types import Message, CallbackQuery
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

from databases.director import database as db

ROLE_BANNED = 5

class BanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None

        if isinstance(event, Message):
            user_id = event.from_user.id

        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if not user_id:
            return await handler(event, data)

        user = await db.get_user_by_telegram(user_id) or {}
        roles = user.get("roles") or []

        if ROLE_BANNED in roles:
            text = "⛔ Sizning akkauntingiz bloklangan!\n\n🛑 Доступ к боту ограничен."
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            elif isinstance(event, Message):
                await event.bot.send_message(event.chat.id, text)
            return None  

        return await handler(event, data)

