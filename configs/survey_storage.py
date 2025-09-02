import asyncio, json
from pathlib import Path
from datetime import datetime, timezone

SURVEY_FILE = Path("configs/data/surveys.json")
SURVEY_FILE.parent.mkdir(parents=True, exist_ok=True)
_LOCK = asyncio.Lock()

def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

async def _read() -> dict:
    if not SURVEY_FILE.exists():
        return {}
    with SURVEY_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

async def _write(data: dict) -> None:
    tmp = SURVEY_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(SURVEY_FILE)

async def add_pending(booking_id: int, user_id: int, telegram_id: int, barber_id: int, send_at_iso_utc: str, lang: str = "🇺🇿 uz") -> None:
    async with _LOCK:
        data = await _read()
        data[str(booking_id)] = {
            "booking_id": booking_id,
            "user_id": user_id,
            "telegram_id": telegram_id,
            "barber_id": barber_id,
            "lang": lang,
            "send_at": send_at_iso_utc,
            "sent": False,
            "created_at": _now_utc_iso(),
        }
        await _write(data)

async def get_due(now_iso_utc: str) -> list[dict]:
    async with _LOCK:
        data = await _read()
        out = []
        for rec in data.values():
            if not rec.get("sent") and rec.get("send_at") <= now_iso_utc:
                out.append(rec)
        return out

async def mark_sent(booking_id: int) -> None:
    async with _LOCK:
        data = await _read()
        key = str(booking_id)
        if key in data:
            data[key]["sent"] = True
            data[key]["sent_at"] = _now_utc_iso()
            await _write(data)

async def remove(booking_id: int) -> None:
    async with _LOCK:
        data = await _read()
        data.pop(str(booking_id), None)
        await _write(data)
