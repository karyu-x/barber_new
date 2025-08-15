import os
import logging
from aiogram.types import Update
from aiohttp import web
from decouple import config

from handlers.register_handlers import bot, dp

logging.basicConfig(
    level=logging.INFO,  # уровень логирования: DEBUG, INFO, WARNING, ERROR
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # вывод в консоль
        logging.FileHandler("bot.log", mode="a", encoding="utf-8")  # запись в файл
    ]
)

logger = logging.getLogger(__name__)

WEBHOOK_PATH = "/webhook"
WEBHOOK_HOST = config("WEBHOOK_URL", default="")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else ""
PORT = int(os.getenv("PORT", "8000"))

async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL, allowed_updates=["message", "callback_query"])
    logger.info("✅ Webhook установлен: %s", WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    if WEBHOOK_URL:
        await bot.delete_webhook()
        logger.info("❌ Webhook удалён")

async def health(_request):
    return web.json_response({"status": "ok"})

async def handle(request):
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.exception("Ошибка обработки запроса: %s", e)
        return web.Response(status=500)
    return web.Response()

def start_webhook():
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_post(WEBHOOK_PATH, handle)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, port=PORT)

if __name__ == "__main__":
    start_webhook()