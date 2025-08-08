import logging
from aiogram.types import Update
from aiohttp import web
from decouple import config

from handlers.register_handlers import bot, dp

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Webhook config
WEBHOOK_PATH = "/webhook"
WEBHOOK_HOST = config("WEBHOOK_URL")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info("✅ Webhook установлен")

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    logger.info("❌ Webhook удалён")

async def handle(request):
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {e}")
        return web.Response(status=500)
    return web.Response()

def start():
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, port=8000)

if __name__ == "__main__":
    start()