from aiogram.types import Update
from aiohttp import web
from handlers.register_handlers import bot, dp
from decouple import config

WEBHOOK_PATH = "/webhook"
WEBHOOK_HOST = config("WEBHOOK_URL")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    print("✅ Webhook установлен")

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    print("❌ Webhook удалён")

async def handle(request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return web.Response()

def start():
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, port=8000)

if __name__ == "__main__":
    start()