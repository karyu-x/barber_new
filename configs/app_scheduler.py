from aiogram import Bot
from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone

from .survey_storage import get_due, mark_sent
from handlers.rate_booking import send_survey_message
from handlers.register_handlers import dp

scheduler: AsyncIOScheduler | None = None

def get_scheduler() -> AsyncIOScheduler:
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    return scheduler


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

async def get_user_context(bot, telegram_id: int) -> FSMContext:
    return dp.fsm.get_context(bot=bot, chat_id=telegram_id, user_id=telegram_id)

async def run_survey_dispatch(bot: Bot):
    due = await get_due(_now_utc_iso())
    for rec in due:
        try:
            ctx = await get_user_context(bot, rec["telegram_id"])
            await send_survey_message(
                bot=bot,
                state=ctx,                    
                user_id=rec["user_id"],
                telegram_id=rec["telegram_id"],
                booking_id=rec["booking_id"],
                barber_id=rec["barber_id"],
                lang=rec.get("lang", "🇺🇿 uz"),
            )
            await mark_sent(rec["booking_id"])
        except Exception as e:
            print(f"[survey] failed for booking {rec['booking_id']}: {e}")

