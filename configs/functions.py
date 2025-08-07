import json
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