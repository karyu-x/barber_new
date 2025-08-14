import json
import random
import asyncio
import logging

from datetime import datetime
from pathlib import Path
from aiogram.types import FSInputFile

logger = logging.getLogger(__name__)

LOGO_PATH = Path("images/logo.png")

def get_logo_file() -> FSInputFile | None:
    if LOGO_PATH.exists():
        return FSInputFile(LOGO_PATH)
    print("❌ Не удалось найти изображение для отправки.")
    return None

def load_translations():
    try:
        with open("configs/datas.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ERROR] Ошибка загрузки перевода: {e}")
        return {}

translations = load_translations()

def get_text(lang: str, *path: str) -> str:
    result = translations.get(lang, {})
    for key in path:
        result = result.get(key, {})
    if isinstance(result, str):
        return result
    return f"[{lang}." + ".".join(path) + "]"

def get_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")

BUTTONS_PATH = Path("configs/buttons.json")

def get_admin_buttons(telegram_id: int):
    try:
        data = json.loads(BUTTONS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error reading buttons from {BUTTONS_PATH}: {e}")
        return []
    return (data.get(str(telegram_id)) or {}).get("buttons", [])

def set_admin_buttons(telegram_id: int, buttons: list[str]) -> None:
    try:
        if BUTTONS_PATH.exists():
            data = json.loads(BUTTONS_PATH.read_text(encoding="utf-8"))
        else:
            data = {}
        
        data[str(telegram_id)] = {"buttons": buttons}

        BUTTONS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"Updated buttons for admin {telegram_id}")
    except Exception as e:
        logger.error(f"Error saving buttons for admin {telegram_id}: {e}")

async def delete_admin_from_json(admin_id: str):
    try:
        if BUTTONS_PATH.exists():
            data = json.loads(BUTTONS_PATH.read_text(encoding="utf-8"))
        else:
            data = {}
        
        if str(admin_id) in data:
            del data[str(admin_id)]  

            BUTTONS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info(f"Admin with ID {admin_id} was deleted successfully.")
            return True
        else:
            logger.warning(f"Admin with ID {admin_id} not found.")
            return False

    except Exception as e:
        logger.error(f"Error deleting admin {admin_id} from JSON: {e}")
        return False

SECRET_MESSAGES = [
    "🔄 Updating interface…",
    "⚙ Switching mode…",
    "🛠 Reconfiguring system…",
    "🔐 Synchronizing settings…",
    "🌀 Loading modules…",
    "📡 Connecting…",
    "🔍 Initializing…",
    "💾 Applying changes…",
    "🤖 Doing robot stuff…",
    "🕵️‍♂️ Secret operation in progress…",
    "💣 Arming lasers…",
    "🧙 Casting spell…",
    "📦 Unpacking resources…",
    "🔧 Calibrating components…",
    "🌌 Accessing deep space channels…"
]

async def get_random_modes(message, user_id, ReplyKeyboardRemove):
    msg = await message.bot.send_message(user_id, random.choice(SECRET_MESSAGES), reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.025)
    await msg.delete()