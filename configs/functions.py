import json
from datetime import datetime
from pathlib import Path
from aiogram.types import FSInputFile

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
    except Exception:
        return []
    return (data.get(str(telegram_id)) or {}).get("buttons", [])

def set_admin_buttons(telegram_id: int, buttons: list[str]) -> None:
    data = {}
    if BUTTONS_PATH.exists():
        try:
            data = json.loads(BUTTONS_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    data[str(telegram_id)] = {"buttons": buttons}
    BUTTONS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
