import json
import random
import asyncio
import logging
import csv
import io

from datetime import datetime, timedelta
from pathlib import Path
from aiogram.types import FSInputFile, BufferedInputFile

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


UZ_DAYS = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
RU_DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

def get_today(lang):
    today = datetime.today()
    if lang == "🇺🇿 uz":
        return f"{today.today:02d}.{today.month:02d} {UZ_DAYS[today.weekday()]}"
    elif lang == "🇷🇺 ru":
        return f"{today.today:02d}.{today.month:02d} {RU_DAYS[today.weekday()]}"

def get_days_from_today(lang: str = "uz"):
    days = []
    today = datetime.today()
    for i in range(30): 
        day = today + timedelta(days=i)
        weekday = day.weekday()  
        if lang == "🇺🇿 uz":
            formatted = f"{day.day:02d}.{day.month:02d} {UZ_DAYS[weekday]}"
        elif lang == "🇷🇺 ru":
            formatted = f"{day.day:02d}.{day.month:02d} {RU_DAYS[weekday]}"
        days.append(formatted)

    return days


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

def generate_clients_csv(clients: list[dict]) -> BufferedInputFile:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Ismi/Имя", "Telefon/Телефон", "Til/Язык", "Bronlar soni/Количество бронов", "Status/Статус"])

    for c in clients:
        status = "⛔️" if 5 in c.get("roles") else "✅"
        writer.writerow([
            c.get("first_name") or "❌",
            c.get("phone_number") or "❌",
            "🇺🇿" if c.get("language") == "uz" else "🇷🇺",
            c.get("total_booking", 0),
            status
        ])

    output.seek(0)
    csv_file = io.BytesIO(output.getvalue().encode("utf-8"))
    csv_file.name = "clients.csv"
    return BufferedInputFile(csv_file.getvalue(), filename="clients.csv")