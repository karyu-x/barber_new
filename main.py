import os
import logging
from json import JSONDecodeError

from aiogram.types import Update
from aiohttp import web
from decouple import config
from pydantic import ValidationError

from handlers.register_handlers import bot, dp
from databases.database import close_session 
from configs.app_scheduler import get_scheduler, run_survey_dispatch


# -------------------- logging --------------------
log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logging.basicConfig(level=logging.INFO, handlers=[console_handler])
logger = logging.getLogger(__name__)


# -------------------- config --------------------
WEBHOOK_SECRET = config("WEBHOOK_SECRET", default="")
WEBHOOK_PATH = f"/webhook/{WEBHOOK_SECRET}" if WEBHOOK_SECRET else "/webhook"

WEBHOOK_HOST = config("WEBHOOK_URL", default="")
WEBHOOK_URL = f"{WEBHOOK_HOST}/webhook" if WEBHOOK_HOST else ""

# -------------------- lifecycle hooks --------------------
async def on_startup(app: web.Application):
    if WEBHOOK_URL:
        sch = get_scheduler()
        try:
            sch.remove_job("survey-pull")
        except Exception:
            pass

        sch.add_job(
            run_survey_dispatch,
            "cron",
            minute="*/30",
            args=[bot],
            id="survey-pull"
        )
        if not sch.running:
            sch.start()

        sch.print_jobs()

        await bot.set_webhook(
            WEBHOOK_URL,
            allowed_updates=["message", "callback_query"]
        )
        logger.info("✅ Webhook установлен: %s", WEBHOOK_URL)
    else:
        logger.warning("⚠️ WEBHOOK_URL не задан — вебхук не будет установлен")


async def on_shutdown(app: web.Application):
    try:
        if WEBHOOK_URL:
            await bot.delete_webhook(drop_pending_updates=False)
            logger.info("❌ Webhook удалён")
    except Exception as e:
        logger.exception("Ошибка при удалении вебхука: %s", e)
    finally:
        try:
            await bot.session.close()
        except Exception:
            pass


async def on_cleanup(app: web.Application):
    try:
        sch = get_scheduler()
        if sch.running:
            sch.shutdown(wait=False)
        await close_session()
    except Exception as e:
        logger.exception("Ошибка при закрытии клиентской сессии: %s", e)


# -------------------- handlers --------------------
async def health(_request: web.Request):
    return web.json_response({"status": "ok"})

async def handle(request: web.Request):
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
    except (JSONDecodeError, ValidationError) as e:
        logger.warning("Некорректный апдейт/JSON: %s", e)
    except Exception as e:
        logger.exception("Ошибка обработки апдейта: %s", e)
        try:
            await bot.send_message(
                chat_id="@logginggs",
                text=f"Ошибка в webhook:\n\n<b>{e}</b>",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return web.Response(status=500, text="error")
    return web.Response(status=200)


# -------------------- app factory --------------------
def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_post(WEBHOOK_PATH, handle)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    app.on_cleanup.append(on_cleanup)
    return app


# -------------------- entrypoint --------------------
if __name__ == "__main__":
    PORT = int(os.getenv("PORT", "8080"))
    web.run_app(create_app(), host="0.0.0.0", port=PORT)
