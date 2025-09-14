import re

from datetime import datetime, date, time
from itertools import groupby
from typing import Optional, Union, Any

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from configs import functions as cf
from databases import database as db
from states import state as st
from keyboards import reply as kb_r

barber_router = Router()
router = barber_router

role = "barber"


## get user infos
async def get_user_context(entity, state):
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    user_id = entity.from_user.id

    if isinstance(entity, Message):
        text = (getattr(entity, "text", "") or "").strip()
        return user_id, data, lang, text

    return user_id, data, lang, None


## Error
async def show_error(entity, state, error_key: str = "unknown_command"):
    user_id, _, lang, action = await get_user_context(entity, state)
    text = cf.get_text(lang, "errors", error_key)
    await entity.bot.send_message(chat_id=user_id, text=text)


## Get booking times
async def get_times_of_bookings(my_infos, date):
    bookings = await db.get_barber_bookings(my_infos.get("id"), date.get("full_date"))
    booking_times = {}
    for booking in bookings:
        if booking.get("status") == "CONFIRMED":
            booking_times[f"🟢 {booking.get('start_time').split('T')[1][:5]}"] = booking
        elif booking.get("status") == "CANCELLED":
            booking_times[f"🔴 {booking.get('start_time').split('T')[1][:5]}"] = booking
        else:
            booking_times[f"🏁 {booking.get('start_time').split('T')[1][:5]}"] = booking
    return booking_times



## Booking info
async def get_booking_info(lang, booking):
    client = booking.get("user")
    service = booking.get("service")
    start_time = booking.get("start_time")
    end_time = booking.get("end_time")
    status = booking.get("status")

    if isinstance(client, int):
        client = await db.get_user_by_id(id=client)
    if isinstance(service, int):
        service = await db.get_barber_service_by_id(service)

    def fmt_time(dt: Union[str, datetime]) -> str:
        if isinstance(dt, datetime):
            return dt.strftime("%d.%m.%Y %H:%M")

        if isinstance(dt, str):
            try:
                t = datetime.fromisoformat(dt)
                return t.strftime("%d.%m.%Y %H:%M")
            except ValueError:
                return dt

        return str(dt)

    if lang == "🇷🇺 ru":
        status_map = {
            "COMPLETED": "✅ Подтверждено",
            "CANCELLED": "❌ Отменено",
            "CONFIRMED": "⏳ В ожидании"
        }
    else:
        status_map = {
            "COMPLETED": "✅ Tasdiqlandi",
            "CANCELLED": "❌ Bekor qilindi",
            "CONFIRMED": "⏳ Kutmoqda"
        }

    data = {
        "id": booking.get("id"),
        "client": client.get("first_name") if client else "❌",
        "service": service.get("name") if service else "❌",
        "price": service.get("price") if service and service.get("price") else "❌",
        "start_time": fmt_time(start_time),
        "end_time": fmt_time(end_time),
        "status": status_map.get(status, status)
    }
    template = cf.get_text(lang, role, "message", "booking_details_msg")
    
    return template.format(**data)


### Get breaks
class BreaksRenderer:
    WEEKDAY = {
        "🇺🇿 uz": ["Dushanba","Seshanba","Chorshanba","Payshanba","Juma","Shanba","Yakshanba"],
        "🇷🇺 ru": ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"],
    }
    LBL = {
        "🇺🇿 uz": {
            "title": "⏸️ Tanaffuslar",
            "none": "Tanaffuslar topilmadi.",
            "reason": "Sabab",
            "duration": "Davomiyligi",
        },
        "🇷🇺 ru": {
            "title": "⏸️ Перерывы",
            "none": "Перерывов не найдено.",
            "reason": "Причина",
            "duration": "Длительность",
        },
    }

    def __init__(self, lang: str = "🇺🇿 uz"):
        self.lang = lang if lang in self.WEEKDAY else "🇺🇿 uz"
        self.labels = self.LBL[self.lang]

    async def render_for_barber(self, barber_id: int) -> str:
        breaks = await db.get_barber_breaks(barber_id)
        return self.render(breaks)

    def render(self, breaks):
        if not breaks:
            return self.labels["none"]

        if isinstance(breaks, dict):
            maybe_list = breaks.get("results") or breaks.get("data")
            if isinstance(maybe_list, list):
                breaks = maybe_list
            else:
                return self.labels["none"]

        if isinstance(breaks, str):
            return self.labels["none"]

        rows = []
        for br in breaks:
            if not isinstance(br, dict):
                continue
            st = self._parse_iso(br.get("start_time", ""))
            en = self._parse_iso(br.get("end_time", ""))
            if not st or not en:
                continue
            dur_min = int((en - st).total_seconds() // 60)
            rows.append({
                "id": br.get("id"),
                "date_key": st.date().isoformat(),
                "date_dt": st,
                "start": st,
                "end": en,
                "reason": (br.get("reason") or "").strip(),
                "dur_min": max(dur_min, 0),
            })

        if not rows:
            return self.labels["none"]

        rows.sort(key=lambda r: (r["date_key"], r["start"]))
        lines = [self.labels["title"], ""]
        for _, group in groupby(rows, key=lambda r: r["date_key"]):
            group = list(group)
            lines.append(f"📅 <b>{self._fmt_date_line(group[0]['date_dt'])}</b>")
            for r in group:
                id_line = f"🆔 ID: <b>{r.get('id', 'N/A')}</b>"
                time_line = f"🟢 {self._hhmm(r['start'])}–{self._hhmm(r['end'])}  •  ⏱ {self._dur_str(r['dur_min'])}"
                if r["reason"]:
                    lines.append(f"{id_line}\n{time_line}\n📝 {self.labels['reason']}: <i>{r['reason']}</i>")
                else:
                    lines.append(f"{id_line}\n{time_line}")
                lines.append("")

        while lines and lines[-1] == "":
            lines.pop()
        return "\n".join(lines)

    def _hhmm(self, dt: datetime) -> str:
        return dt.strftime("%H:%M")

    def _fmt_date_line(self, dt: datetime) -> str:
        wd = self.WEEKDAY[self.lang][dt.weekday()]
        return dt.strftime("%d.%m.%Y") + f" • {wd}"

    def _dur_str(self, minutes: int) -> str:
        h, m = divmod(minutes, 60)
        if self.lang == "🇷🇺 ru":
            if h and m: return f"{h} ч {m} мин"
            if h:       return f"{h} ч"
            return f"{m} мин"
        # UZ
        if h and m: return f"{h} soat {m} daqiqa"
        if h:       return f"{h} soat"
        return f"{m} daqiqa"

    @staticmethod
    def _parse_iso(s: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None


## Get break
def get_break_info(break_info, lang):
    start_time = BreaksRenderer._parse_iso(break_info.get("start_time"))
    end_time = BreaksRenderer._parse_iso(break_info.get("end_time"))
    reason = break_info.get("reason", "N/A")
    duration_minutes = int((end_time - start_time).total_seconds() // 60) if start_time and end_time else 0
    msg = (
        f"🆔 ID: <b>{break_info.get('id', 'N/A')}</b>\n"
        f"🕒 {start_time.strftime('%d.%m.%Y %H:%M')} - {end_time.strftime('%H:%M')}\n"
        f"⏱ {duration_minutes} мин\n"
        f"{f'📝 Причина: <i>{reason}</i>' if lang == '🇷🇺 ru' else f'📝 Sababi: <i>{reason}</i>'}"
    )

    return msg


## Get labels
def get_labels(lang: str) -> dict[str, Any]:
    lbl: dict[str, dict[str, str]] = {
        "🇺🇿 uz": {
            "title": "💈 <b>Xizmat turlari va xizmatlar</b>",
            "no_types": "❌ Xizmat turlari topilmadi.",
            "no_services": "❌ Xizmatlar yo‘q",
            "price": "💵",
            "duration": "⏱",
            "desc": "📝",
            "currency": "so‘m",
            "dash": "—",
        },
        "🇷🇺 ru": {
            "title": "💈 <b>Типы услуг и сервисы</b>",
            "no_types": "❌ Типы услуг не найдены.",
            "no_services": "❌ Нет услуг",
            "price": "💵",
            "duration": "⏱",
            "desc": "📝",
            "currency": "сум",
            "dash": "—",
        },
    }

    labels = lbl.get(lang, lbl["🇺🇿 uz"])

    def fmt_price(value: Optional[float | int | str]) -> str:
        if value in (None, ""):
            return labels["dash"]
        try:
            return f"{int(value):,} {labels['currency']}".replace(",", " ")
        except (ValueError, TypeError):
            return f"{value} {labels['currency']}"

    def fmt_duration(d: Optional[str]) -> str:
        if not d:
            return labels["dash"]
        parts = str(d).split(":")
        return ":".join(parts[:2]) if len(parts) >= 2 else str(d)

    def fmt_desc(t: Optional[str]) -> str:
        t = (t or "").strip()
        return t or labels["dash"]

    return {
        **labels,  # базовые тексты
        "fmt_price": fmt_price,
        "fmt_duration": fmt_duration,
        "fmt_desc": fmt_desc,
    }


## Get types and services
async def get_types_and_services_info(lang: str, barber_id: int) -> str:
    types_and_services = await db.get_barber_types_and_services(barber_id)
    labels = get_labels(lang)

    if not types_and_services:
        return labels["no_types"]

    lines: list[str] = [labels["title"], ""]
    for t in types_and_services:
        type_name = (t.get("name") or "").strip() or labels["dash"]
        lines.append(f"🆔 ID: <b>{t.get('id', '❌')}</b>\n📂 <b>{type_name}</b>")

        services = t.get("services") or []
        if not services:
            lines.append(f"   {labels['no_services']}")
            lines.append("")
            continue

        for s in services:
            s_name = (s.get("name") or "").strip() or labels["dash"]
            s_price = labels["fmt_price"](s.get("price"))
            s_dur = labels["fmt_duration"](s.get("duration"))
            s_desc = labels["fmt_desc"](s.get("description"))

            lines.append(
                "   • <b>{name}</b>\n"
                "     {price} {price_val}\n"
                "     {dur} {dur_val}\n"
                "     {desc} {desc_val}".format(
                    name=s_name,
                    price=labels["price"], price_val=s_price,
                    dur=labels["duration"], dur_val=s_dur,
                    desc=labels["desc"], desc_val=s_desc,
                )
            )
        lines.append("")

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)


## Get service info
def get_service_info(lang, service_data):
    labels = get_labels(lang)
    service_info = (
        f"🆔 ID: <b>{service_data.get('id', 'N/A')}</b>\n"
        f"📂 <b>{service_data.get('name', '❌')}</b>\n"
        f"{labels['price']}: <b>{labels['fmt_price'](service_data.get('price'))}</b>\n"
        f"{labels['duration']}: <b>{labels['fmt_duration'](service_data.get('duration'))}</b>\n"
        f"{labels['desc']}: <b>{labels['fmt_desc'](service_data.get('description'))}</b>\n"
    )
    return service_info


## Get cabinet info
async def get_cabinet_info(my_infos, lang):
    rating = await db.get_barber_rating_by_id(my_infos.get("id"))
    if not rating:
        rating = {"rating": "❌"}
    cabinet_info = (
        f"🆔 ID: <b>{my_infos.get('id', 'N/A')}</b>\n"
        f"🛩 {'Телеграм ID' if lang == '🇷🇺 ru' else 'Telegram ID'}: <b>{my_infos.get('telegram_id', '❌')}</b>\n"
        f"👤 {'Имя' if lang == '🇷🇺 ru' else 'Ism'}: <b>{my_infos.get('first_name', '❌')}</b>\n"
        f"📞 {'Телефон' if lang == '🇷🇺 ru' else 'Telefon'}: <b>{my_infos.get('phone_number', '❌')}</b>\n"
        f"📝 {'Описание' if lang == '🇷🇺 ru' else 'Tavsif'}: <b>{my_infos.get('description', '❌')}</b>\n"
        f"⭐ {'Рейтинг' if lang == '🇷🇺 ru' else 'Reyting'}: <b>{rating.get('rating', '❌')}</b>\n"
        f"🕒 {'Время работы' if lang == '🇷🇺 ru' else 'Ish vaqti'}: <b>{my_infos.get('default_from_hour', '❌')} - {my_infos.get('default_to_hour', '❌')}</b>\n"
    )

    if my_infos.get("photo"):
        cabinet_info += f"🖼 {'Фото' if lang == '🇷🇺 ru' else 'Rasm'}: ✅\n"
    else:
        cabinet_info += f"🖼 {'Фото' if lang == '🇷🇺 ru' else 'Rasm'}: ❌\n"
    return cabinet_info


@router.message(st.barber.main_menu)
async def show_main_menu(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "bookings"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "bookings_msg"),
            reply_markup=kb_r.br_bookings(lang)
        )
        await state.set_state(st.barber.bookings)

    elif text == cf.get_text(lang, role, "button", "breaks"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "breaks_msg"),
            reply_markup=kb_r.br_breaks(lang)
        )
        await state.set_state(st.barber.breaks)

    elif text == cf.get_text(lang, role, "button", "types"):
        await message.bot.send_message(
            chat_id=user_id,
            text=await get_types_and_services_info(lang, my_infos.get("telegram_id")),
            parse_mode="HTML",
            reply_markup=await kb_r.br_types(lang, my_infos.get("telegram_id"))
        )
        await state.set_state(st.barber.types)

    elif text == cf.get_text(lang, role, "button", "cabinet"):
        msg = await get_cabinet_info(my_infos, lang)
        if my_infos.get("photo"):
            await message.bot.send_photo(
                chat_id=user_id,
                photo=my_infos.get("photo"),
                caption=msg,
                parse_mode="HTML",
                reply_markup=kb_r.br_cabinet(lang)
            )
    
        else:
            await message.bot.send_message(
                chat_id=user_id,
                text=msg,
                parse_mode="HTML",
                reply_markup=kb_r.br_cabinet(lang)
            )

        await state.set_state(st.barber.cabinet)

    elif text == cf.get_text(lang, role, "button", "user_menu"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.us_main_menu(lang, my_infos.get("roles"))
        )
        await state.set_state(st.user.main_menu)

    else:
        await show_error(message, state)


@router.message(st.barber.bookings)
async def show_bookings(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    date = cf.get_today(lang)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    elif text == cf.get_text(lang, role, "button", "bookings_today"):
        bookings = await get_times_of_bookings(my_infos, date)
        if bookings:
            await message.bot.send_message(
                chat_id=user_id,
                text=cf.get_text(lang, role, "message", "bookings_today_msg"),
                reply_markup=kb_r.br_bookings_today(lang, bookings)
            )
            await state.set_state(st.barber.bookings_today)

        else:
            await message.bot.send_message(
                chat_id=user_id,
                text=cf.get_text(lang, role, "message", "bookings_none_msg"),
            )

    elif text == cf.get_text(lang, role, "button", "bookings_otherday"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "bookings_otherday_msg"),
            reply_markup=kb_r.br_bookings_otherday(lang)
        )
        await state.set_state(st.barber.bookings_otherday)
    
    else:
        await show_error(message, state)


@router.message(st.barber.bookings_today)
async def show_bookings_today(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    day = data.get("selected_day")
    date = cf.get_today(lang) if not day else day
    my_infos = data.get("my_infos")
    back_state = data.get("back_state")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "bookings_msg") if back_state != "otherday" else cf.get_text(lang, role, "message", "bookings_otherday_msg"),
            reply_markup=kb_r.br_bookings(lang) if back_state != "otherday" else kb_r.br_bookings_otherday(lang)
        )
        await state.set_state(st.barber.bookings if back_state != "otherday" else st.barber.bookings_otherday)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        bookings = await get_times_of_bookings(my_infos, date)

        if text in bookings:
            booking = bookings.get(text)
            msg = await get_booking_info(lang, booking)
            await message.bot.send_message(
                user_id,
                msg,
                parse_mode="HTML"
            )
        
        else:
            await show_error(message, state)


@router.message(st.barber.bookings_otherday)
async def show_bookings_otherday(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "bookings_msg"),
            reply_markup=kb_r.br_bookings(lang)
        )
        await state.set_state(st.barber.bookings)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        days = cf.get_days_from_today(lang)
        selected_day = None
        for day in days:
            if text == day.get("date"):
                await state.update_data(selected_day=day,
                                        back_state="otherday")
                selected_day = day
                break

        if selected_day:
            bookings = await get_times_of_bookings(my_infos, selected_day)
            if bookings:
                await message.bot.send_message(
                    user_id,
                    cf.get_text(lang, role, "message", "bookings_otherday_next_msg"),
                    reply_markup=kb_r.br_bookings_today(lang, bookings)
                )
                await state.set_state(st.barber.bookings_today)

            else:
                await message.bot.send_message(
                    chat_id=user_id,
                    text=cf.get_text(lang, role, "message", "bookings_none_msg"),
                )     

        else:
            await show_error(message, state)


@router.message(st.barber.breaks)
async def show_breaks(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "breaks_all"):
        renderer = BreaksRenderer(lang)
        breaks_text = await renderer.render_for_barber(my_infos.get("id"))
        await message.bot.send_message(
            user_id,
            breaks_text,
            parse_mode="HTML"
        )

    elif text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    elif text == cf.get_text(lang, role, "button", "break_add"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "break_add_reason_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.break_add_reason)

    elif text == cf.get_text(lang, role, "button", "break_edit"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "break_edit_msg"),
            reply_markup=await kb_r.break_buttons(lang, my_infos["id"])
        )
        await state.set_state(st.barber.break_edit)

    elif text == cf.get_text(lang, role, "button", "break_delete"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "break_delete_msg"),
            reply_markup=await kb_r.break_buttons(lang, my_infos["id"])
        )
        await state.set_state(st.barber.break_delete)

    else:
        await show_error(message, state)


@router.message(st.barber.break_add_reason)
async def add_break(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "breaks_msg"),
            reply_markup=kb_r.br_breaks(lang)
        )
        await state.set_state(st.barber.breaks)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        await state.update_data(break_reason=text)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "break_add_time_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.break_add_time)


@router.message(st.barber.break_add_time)
async def add_break_time(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")
    reason = data.get("break_reason")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "break_add_reason_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.update_data(break_reason=None)
        await state.set_state(st.barber.break_add_reason)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.update_data(break_reason=None)
        await state.set_state(st.barber.main_menu)

    else:

        pattern_with_date = r"^(\d{2}-\d{2})\s+(\d{2}:\d{2})-(\d{2}:\d{2})$"
        pattern_today     = r"^(\d{2}:\d{2})-(\d{2}:\d{2})$"

        day = date.today()
        m = re.match(pattern_with_date, text) or re.match(pattern_today, text)
        if not m:
            await show_error(message, state, "invalid_time_range_msg")
            return

        if len(m.groups()) == 3:
            day_str, from_hour, to_hour = m.groups()
            try:
                day = datetime.strptime(day_str, "%d-%m").date().replace(year=date.today().year)
            except Exception:
                await show_error(message, state, "invalid_date_format_msg")
                return
        else:
            from_hour, to_hour = m.groups()

        try:
            h1, m1 = map(int, from_hour.split(":"))
            h2, m2 = map(int, to_hour.split(":"))
            start_dt = datetime.combine(day, time(h1, m1))
            end_dt   = datetime.combine(day, time(h2, m2))
            if end_dt <= start_dt:
                raise ValueError
        except Exception:
            await show_error(message, state, "invalid_time_range_msg")
            return

        start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
        end_str   = end_dt.strftime("%Y-%m-%dT%H:%M:%S")

        payload = {
            "start_time": start_str,
            "end_time": end_str,
            "barber": my_infos.get("id"),
            "reason": reason
        }

        await state.update_data(break_datas=payload)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "break_add_confirm_msg"),
            reply_markup=kb_r.confirm_reject(lang)
        )
        await state.set_state(st.barber.break_add_confirm)


@router.message(st.barber.break_add_confirm)
async def confirm_add_break(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    datas = data.get("break_datas")

    if text == cf.get_text(lang, role, "button", "confirm"):
        await db.create_barber_break(datas)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "break_add_success_msg"),
            reply_markup=kb_r.br_breaks(lang)
        )
        await state.set_state(st.barber.breaks)

    elif text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "break_add_time_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.break_add_time)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)
    else:
        await show_error(message, state)

    await state.update_data(break_datas=None)


@router.message(st.barber.break_edit)
async def edit_break(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "breaks_msg"),
            reply_markup=kb_r.br_breaks(lang)
        )
        await state.set_state(st.barber.breaks)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:

        if text[0].isdigit():
            barber_break = await db.get_barber_break_by_id(text, my_infos.get("id"))

            if barber_break:
                await state.update_data(break_data=barber_break)
                break_msg = get_break_info(barber_break, lang)
                await message.bot.send_message(
                    chat_id=user_id,
                    text=f'{break_msg}\n\n{cf.get_text(lang, role, "message", "break_edit_time_msg")}',
                    parse_mode="HTML",
                    reply_markup=kb_r.back_main(lang)
                )
                await state.set_state(st.barber.break_edit_time)

            else:
                await show_error(message, state)

        else:
            await show_error(message, state)


@router.message(st.barber.break_edit_time)
async def edit_break_time(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    break_data = data.get("break_data")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "breaks_msg"),
            reply_markup=kb_r.br_breaks(lang)
        )
        await state.set_state(st.barber.breaks)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        if not break_data:
            await show_error(message, state, "no_break_data_msg")
            return

        start_time = BreaksRenderer._parse_iso(break_data.get("start_time"))

        try:
            h, m = map(int, text.split(":"))
            end_time = datetime.combine(
                start_time.date(), time(h, m)
            ).replace(tzinfo=start_time.tzinfo)

            if end_time <= start_time:
                await show_error(message, state, "end_time_must_be_after_start_time_msg")
                return

        except ValueError:
            await show_error(message, state, "invalid_time_format_msg")
            return

        break_data["end_time"] = end_time.isoformat()
        await state.update_data(break_data=break_data)

        await db.update_barber_break_by_id(
            break_data.get("id"), data={"end_time": end_time.isoformat()}
        )

        await message.bot.send_message(
            user_id, cf.get_text(lang, role, "message", "break_edit_success_msg")
        )
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "breaks_msg"),
            reply_markup=kb_r.br_breaks(lang),
        )
        await state.set_state(st.barber.breaks)

    await state.update_data(break_data=None)


@router.message(st.barber.break_delete)
async def delete_break(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "breaks_msg"),
            reply_markup=kb_r.br_breaks(lang)
        )
        await state.set_state(st.barber.breaks)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:

        if text[0].isdigit():
            barber_break = await db.get_barber_break_by_id(text, my_infos.get("id"))

            if barber_break:
                await state.update_data(break_data=barber_break)
                break_msg = get_break_info(barber_break, lang)
                await message.bot.send_message(
                    chat_id=user_id,
                    text=f'{break_msg}\n\n{cf.get_text(lang, role, "message", "break_delete_confirm_msg")}',
                    parse_mode="HTML",
                    reply_markup=kb_r.confirm_reject(lang)
                )
                await state.set_state(st.barber.break_delete_confirm)

            else:
                await message.bot.send_message(
                    chat_id=user_id,
                    text=cf.get_text(lang, role, "message", "break_not_found_msg")
                )

        else:
            await show_error(message, state)


@router.message(st.barber.break_delete_confirm)
async def confirm_delete_break(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    break_data = data.get("break_data")

    if text == cf.get_text(lang, role, "button", "confirm"):
        await db.delete_barber_break_by_id(break_data.get("id"))
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "break_delete_success_msg"),
            reply_markup=kb_r.br_breaks(lang)
        )
        await state.set_state(st.barber.breaks)

    elif text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "breaks_msg"),
            reply_markup=kb_r.br_breaks(lang)
        )
        await state.set_state(st.barber.breaks)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        await show_error(message, state)

    await state.update_data(break_data=None)


@router.message(st.barber.cabinet)
async def show_cabinet(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    elif text == cf.get_text(lang, role, "button", "phone_edit"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "phone_edit_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.cabinet_phone)

    elif text == cf.get_text(lang, role, "button", "about_edit"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "about_edit_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.cabinet_about)

    elif text == cf.get_text(lang, role, "button", "photo_edit"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "photo_edit_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.cabinet_photo)

    elif text == cf.get_text(lang, role, "button", "time_edit"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "time_edit_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.cabinet_time)

    elif text == cf.get_text(lang, role, "button", "language_edit"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "language_edit_msg"),
            reply_markup=kb_r.br_cabinet_language(lang)
        )
        await state.set_state(st.barber.cabinet_language)

    else:
        await show_error(message, state)


@router.message(st.barber.cabinet_phone)
async def edit_phone(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text= await get_cabinet_info(my_infos, lang),
            parse_mode="HTML",
            reply_markup=kb_r.br_cabinet(lang)
        )
        await state.set_state(st.barber.cabinet)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        phone = text.replace(" ", "").replace("-", "")
        if not re.fullmatch(r"(\+?998\d{9})", phone):
            await show_error(message, state, "invalid_phone_number_msg")
            return

        my_infos["phone_number"] = phone
        await db.update_barber_by_id(my_infos.get("id"), {"phone_number": my_infos.get("phone_number")})
        await message.bot.send_message(
            chat_id=user_id,
            text= await get_cabinet_info(my_infos, lang),
            parse_mode="HTML",
            reply_markup=kb_r.br_cabinet(lang)
        )
        await state.set_state(st.barber.cabinet)

    
@router.message(st.barber.cabinet_about)
async def edit_about(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text= await get_cabinet_info(my_infos, lang),
            parse_mode="HTML",
            reply_markup=kb_r.br_cabinet(lang)
        )
        await state.set_state(st.barber.cabinet)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        my_infos["description"] = text
        await db.update_barber_by_id(my_infos.get("id"), {"description": my_infos.get("description")})
        await message.bot.send_message(
            chat_id=user_id,
            text= await get_cabinet_info(my_infos, lang),
            parse_mode="HTML",
            reply_markup=kb_r.br_cabinet(lang)
        )
        await state.set_state(st.barber.cabinet)


@router.message(st.barber.cabinet_photo)
async def edit_photo(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text= await get_cabinet_info(my_infos, lang),
            parse_mode="HTML",
            reply_markup=kb_r.br_cabinet(lang)
        )
        await state.set_state(st.barber.cabinet)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:

        if not message.photo:
            await show_error(message, state, "invalid_photo_msg")
            return

        my_infos["photo"] = message.photo[-1].file_id
        await db.update_barber_by_id(my_infos.get("id"), {"photo": my_infos.get("photo")})
        await message.bot.send_message(
            chat_id=user_id,
            text= await get_cabinet_info(my_infos, lang),
            parse_mode="HTML",
            reply_markup=kb_r.br_cabinet(lang)
        )
        await state.set_state(st.barber.cabinet)


@router.message(st.barber.cabinet_time)
async def edit_time(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text= await get_cabinet_info(my_infos, lang),
            parse_mode="HTML",
            reply_markup=kb_r.br_cabinet(lang)
        )
        await state.set_state(st.barber.cabinet)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:

        if not re.match(r"^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}$", text):
            await show_error(message, state, "invalid_time_range_msg")
            return

        try:
            from_hour, to_hour = [t.strip() for t in text.split("-")]
            h1, m1 = map(int, from_hour.split(":"))
            h2, m2 = map(int, to_hour.split(":"))
            if not (0 <= h1 < 24 and 0 <= h2 < 24 and 0 <= m1 < 60 and 0 <= m2 < 60):
                raise ValueError
        except ValueError:
            await show_error(message, state, "invalid_time_range_msg")
            return

        my_infos["default_from_hour"] = from_hour
        my_infos["default_to_hour"] = to_hour

        datas = {
            "from_hour": from_hour,
            "to_hour": to_hour
        }
        await db.update_working_hours_by_id(my_infos["id"], datas)

        await message.bot.send_message(
            chat_id=user_id,
            text= await get_cabinet_info(my_infos, lang),
            parse_mode="HTML",
            reply_markup=kb_r.br_cabinet(lang)
        )
        await state.update_data(my_infos=my_infos)
        await state.set_state(st.barber.cabinet)


@router.message(st.barber.cabinet_language)
async def edit_language(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text= await get_cabinet_info(my_infos, lang),
            parse_mode="HTML",
            reply_markup=kb_r.br_cabinet(lang)
        )
        await state.set_state(st.barber.cabinet)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    elif text in ["🇺🇿 uz", "🇷🇺 ru"]:
        await db.update_barber_by_id(my_infos.get("id"), {"language": "uz" if text.endswith("uz") else "ru"})
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(text, role, "message", "language_selected_msg"),
            reply_markup=kb_r.br_cabinet(text)
        )
        await state.set_state(st.barber.cabinet)
    
    else:
        await show_error(message, state)


@router.message(st.barber.types)
async def show_types(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    elif text == cf.get_text(lang, role, "button", "type_add"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "type_add_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.type_add)

    elif text == cf.get_text(lang, role, "button", "type_delete"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "type_delete_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.type_delete)

    else:
        type_id = text.split(" - ")[0].split()[1]
        type_data = await db.get_barber_type_by_id(type_id)

        if type_data:
            await state.update_data(type_data=type_data)
            await message.bot.send_message(
                chat_id=user_id,
                text=cf.get_text(lang, role, "message", "services_msg"),
                reply_markup=await kb_r.br_services(lang, type_data.get("id"))
            )
            await state.set_state(st.barber.services)

        else:
            await show_error(message, state)


@router.message(st.barber.type_add)
async def add_type(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=await get_types_and_services_info(lang, my_infos.get("telegram_id")),
            parse_mode="HTML",
            reply_markup=await kb_r.br_types(lang, my_infos.get("telegram_id"))
        )
        await state.set_state(st.barber.types)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        datas = {
            "name": text.strip(),
            "barber": my_infos.get("id")
        }
        await db.create_barber_type(datas)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "type_added_msg"),
            reply_markup=await kb_r.br_types(lang, my_infos.get("telegram_id"))
        )
        await message.bot.send_message(
            chat_id=user_id,
            text=await get_types_and_services_info(lang, my_infos.get("telegram_id")),
            parse_mode="HTML"
        )
        await state.set_state(st.barber.types)


@router.message(st.barber.type_delete)
async def delete_type(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=await get_types_and_services_info(lang, my_infos.get("telegram_id")),
            parse_mode="HTML",
            reply_markup=await kb_r.br_types(lang, my_infos.get("telegram_id"))
        )
        await state.set_state(st.barber.types)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:

        if text.isdigit():
            type_data = await db.get_barber_type_by_id(text)

            if type_data:
                await state.update_data(type_data=type_data)
                await message.bot.send_message(
                    chat_id=user_id,
                    text=cf.get_text(lang, role, "message", "type_delete_confirm_msg"),
                    reply_markup=kb_r.confirm_reject(lang)
                )
                await state.set_state(st.barber.type_delete_confirm)

            else:
                await message.bot.send_message(
                    chat_id=user_id,
                    text=cf.get_text(lang, role, "message", "type_not_found_msg")
                )

        else:
            await show_error(message, state)


@router.message(st.barber.type_delete_confirm)
async def confirm_delete_type(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")
    type_data = data.get("type_data")

    if text == cf.get_text(lang, role, "button", "confirm"):
        await db.delete_barber_type_by_id(type_data.get("id"))
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "type_delete_success_msg").format(type_name=type_data.get("name")),
            reply_markup=await kb_r.br_types(lang, my_infos.get("telegram_id"))
        )
        await message.bot.send_message(
            chat_id=user_id,
            text=await get_types_and_services_info(lang, my_infos.get("telegram_id")),
            parse_mode="HTML"
        )
        await state.set_state(st.barber.types)

    elif text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=await get_types_and_services_info(lang, my_infos.get("telegram_id")),
            parse_mode="HTML",
            reply_markup=await kb_r.br_types(lang, my_infos.get("telegram_id"))
        )
        await state.set_state(st.barber.types)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        await show_error(message, state)

    await state.update_data(type_data=None)


@router.message(st.barber.services)
async def show_services(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=await get_types_and_services_info(lang, my_infos.get("telegram_id")),
            parse_mode="HTML",
            reply_markup=await kb_r.br_types(lang, my_infos.get("telegram_id"))
        )
        await state.set_state(st.barber.types)
    
    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    elif text == cf.get_text(lang, role, "button", "service_add"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_add_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.service_add)

    elif text == cf.get_text(lang, role, "button", "service_delete"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_delete_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.service_delete)

    else:
        service_id = text.split(" - ")[0].split()[1]
        service_data = await db.get_barber_service_by_id(service_id)

        if service_data:
            await state.update_data(service_data=service_data)
            await message.bot.send_message(
                chat_id=user_id,
                text=get_service_info(lang, service_data),
                parse_mode="HTML",
                reply_markup=kb_r.br_service_detail(lang)
            )
            await state.set_state(st.barber.service_detail)

        else:
            await show_error(message, state)


@router.message(st.barber.service_add)
async def add_service(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    type_data = data.get("type_data")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "services_msg"),
            reply_markup=await kb_r.br_services(lang, type_data.get("id"))
        )
        await state.set_state(st.barber.services)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        datas = {
            "name": text.strip(),
            "service_type": type_data.get("id")
        }
        await db.create_barber_service(datas)
        await message.bot.send_message(
            chat_id=user_id,
            text=f'{cf.get_text(lang, role, "message", "service_added_msg")}\n\n{cf.get_text(lang, role, "message", "services_msg")}',
            reply_markup=await kb_r.br_services(lang, type_data.get("id"))
        )
        await state.set_state(st.barber.services)


@router.message(st.barber.service_delete)
async def delete_service(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    type_data = data.get("type_data")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "services_msg"),
            reply_markup=await kb_r.br_services(lang, type_data.get("id"))
        )
        await state.set_state(st.barber.services)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
    
        if text.isdigit():
            service_data = await db.get_barber_service_by_id(text)

            if service_data:
                await state.update_data(service_data=service_data)
                await message.bot.send_message(
                    chat_id=user_id,
                    text=cf.get_text(lang, role, "message", "service_delete_confirm_msg"),
                    reply_markup=kb_r.confirm_reject(lang)
                )
                await state.set_state(st.barber.service_delete_confirm)

            else:
                await message.bot.send_message(
                    chat_id=user_id,
                    text=cf.get_text(lang, role, "message", "service_not_found_msg")
                )

        else:
            await show_error(message, state)


@router.message(st.barber.service_delete_confirm)
async def confirm_service_delete(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    service_data = data.get("service_data")
    type_data = data.get("type_data")

    if text == cf.get_text(lang, role, "button", "confirm"):
        await db.delete_barber_service_by_id(service_data.get("id"))
        await message.bot.send_message(
            chat_id=user_id,
            text=f'{cf.get_text(lang, role, "message", "service_delete_success_msg").format(service_name=service_data.get("name"))}\n\n{cf.get_text(lang, role, "message", "services_msg")}',
            reply_markup=await kb_r.br_services(lang, type_data.get("id"))
        )
        await state.set_state(st.barber.services)

    elif text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "services_msg"),
            reply_markup=await kb_r.br_services(lang, type_data.get("id"))
        )
        await state.set_state(st.barber.services)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        await show_error(message, state)

    await state.update_data(service_data=None)


@router.message(st.barber.service_detail)
async def show_service_detail(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    type_data = data.get("type_data")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "services_msg"),
            reply_markup=await kb_r.br_services(lang, type_data.get("id"))
        )
        await state.set_state(st.barber.services)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    elif text == cf.get_text(lang, role, "button", "name_edit"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "name_edit_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.service_name)

    elif text == cf.get_text(lang, role, "button", "description_edit"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "description_edit_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.service_description)

    elif text == cf.get_text(lang, role, "button", "duration_edit"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "duration_edit_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.service_duration)

    elif text == cf.get_text(lang, role, "button", "price_edit"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "price_edit_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.barber.service_price)

    else:
        await show_error(message, state)


@router.message(st.barber.service_name)
async def edit_service_name(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    service_data = data.get("service_data")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            parse_mode="HTML",
            text=get_service_info(lang, service_data),
            reply_markup=kb_r.br_service_detail(lang)
        )
        await state.set_state(st.barber.service_detail)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        service_data["name"] = text.strip()
        await db.update_barber_service_by_id(service_data.get("id"), {"name": service_data.get("name")})
        await message.bot.send_message(
            chat_id=user_id,
            text=get_service_info(lang, service_data),
            parse_mode="HTML",
            reply_markup=kb_r.br_service_detail(lang)
        )
        await state.set_state(st.barber.service_detail)


@router.message(st.barber.service_description)
async def edit_service_description(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    service_data = data.get("service_data")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            parse_mode="HTML",
            text=get_service_info(lang, service_data),
            reply_markup=kb_r.br_service_detail(lang)
        )
        await state.set_state(st.barber.service_detail)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        service_data["description"] = text.strip()
        await db.update_barber_service_by_id(service_data.get("id"), {"description": service_data.get("description")})
        await message.bot.send_message(
            chat_id=user_id,
            text=get_service_info(lang, service_data),
            parse_mode="HTML",
            reply_markup=kb_r.br_service_detail(lang)
        )
        await state.set_state(st.barber.service_detail)


@router.message(st.barber.service_duration)
async def edit_service_duration(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    service_data = data.get("service_data")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            parse_mode="HTML",
            text=get_service_info(lang, service_data),
            reply_markup=kb_r.br_service_detail(lang)
        )
        await state.set_state(st.barber.service_detail)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        try:
            if ":" in text:
                h, m = map(int, text.split(":"))
                if not (0 <= h < 24 and 0 <= m < 60):
                    raise ValueError
                minutes_total = h * 60 + m
            else:
                minutes_total = int(text)
                if not (1 <= minutes_total <= 1439):  
                    raise ValueError
                
        except ValueError:
            await message.bot.send_message(
                user_id,
                cf.get_text(lang, "errors", "invalid_duration_msg"),
                parse_mode="HTML"
            )
            return

        h, m = divmod(minutes_total, 60)
        duration_str = f"{h:02d}:{m:02d}:00"

        service_data["duration"] = duration_str
        await db.update_barber_service_by_id(service_data.get("id"), {"duration": service_data.get("duration")})
        await message.bot.send_message(
            chat_id=user_id,
            text=get_service_info(lang, service_data),
            parse_mode="HTML",
            reply_markup=kb_r.br_service_detail(lang)
        )
        await state.set_state(st.barber.service_detail)


@router.message(st.barber.service_price)
async def edit_service_price(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    service_data = data.get("service_data")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            parse_mode="HTML",
            text=get_service_info(lang, service_data),
            reply_markup=kb_r.br_service_detail(lang)
        )
        await state.set_state(st.barber.service_detail)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        def _parse_price(s: str) -> int | None:
            price_re = re.compile(r"\d+")
            digits = "".join(price_re.findall(s))
            if not digits:
                return None
            return int(digits)

        price = _parse_price(text)
        if not price or price <= 0:
            await message.bot.send_message(
                user_id,
                cf.get_text(lang, "errors", "invalid_price_msg"),
                parse_mode="HTML"
            )
            return

        service_data["price"] = price
        await db.update_barber_service_by_id(service_data.get("id"), {"price": service_data.get("price")})
        await message.bot.send_message(
            chat_id=user_id,
            text=get_service_info(lang, service_data),
            parse_mode="HTML",
            reply_markup=kb_r.br_service_detail(lang)
        )
        await state.set_state(st.barber.service_detail)