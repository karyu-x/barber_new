import asyncio
import time

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from databases import database as db

ROLE_BANNED = 5

class BanMiddleware(BaseMiddleware):
    def __init__(self, ttl_seconds: int = 45, db_timeout: float = 0.6):
        self.ttl = ttl_seconds
        self.db_timeout = db_timeout
        self.cache: dict[int, tuple[bool, float, dict]] = {}

    def _cache_get(self, uid: int):
        item = self.cache.get(uid)
        if not item:
            return None, None
        is_banned, exp, user = item
        if exp < time.monotonic():
            self.cache.pop(uid, None)
            return None, None
        return is_banned, user

    def _cache_set(self, uid: int, is_banned: bool, user: dict):
        self.cache[uid] = (is_banned, time.monotonic() + self.ttl, user or {})

    def invalidate(self, uid: int):
        self.cache.pop(uid, None)

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            uid = event.from_user.id
        elif isinstance(event, CallbackQuery):
            uid = event.from_user.id
        else:
            return await handler(event, data)

        is_banned, user = self._cache_get(uid)

        if is_banned is None:
            try:
                user = await asyncio.wait_for(db.get_user_by_telegram(uid), timeout=self.db_timeout)
            except Exception:
                user = {}
            roles = (user or {}).get("roles") or []
            is_banned = ROLE_BANNED in roles
            self._cache_set(uid, is_banned, user)

        data["user"] = user

        if is_banned:
            text = "⛔ Sizning akkauntingiz bloklangan!\n\n🛑 Доступ к bоtga cheklangan."
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            else: 
                await event.bot.send_message(event.chat.id, text)
            return  

        return await handler(event, data)