import asyncio, re

from datetime import datetime, date, time, timezone, timedelta
from itertools import groupby
from typing import Any, Iterable, Optional

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import datetime

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

    def fmt_time(dt):
        try:
            t = datetime.fromisoformat(dt)
            return t.strftime("%d.%m.%Y %H:%M")
        except Exception:
            return dt

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

    # ---------- публичные методы ----------

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

    # ---------- приватные хелперы ----------

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


## Get cabinet info
def get_cabinet_info(my_infos, lang):
    cabinet_info = (
        f"🆔 ID: <b>{my_infos.get('id', 'N/A')}</b>\n"
        f"👤 {'Имя' if lang == '🇷🇺 ru' else 'Ism'}: <b>{my_infos.get('first_name', '❌')}</b>\n"
        f"📞 {'Телефон' if lang == '🇷🇺 ru' else 'Telefon'}: <b>{my_infos.get('phone_number', '❌')}</b>\n"
        f"📝 {'Описание' if lang == '🇷🇺 ru' else 'Tavsif'}: <b>{my_infos.get('description', '❌')}</b>\n"
        f"⭐ {'Рейтинг' if lang == '🇷🇺 ru' else 'Reyting'}: <b>{my_infos.get('rating', '❌')}</b>\n"
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
            text=cf.get_text(lang, role, "message", "types_msg"),
            reply_markup=await kb_r.br_types(lang, my_infos.get("barber_id"))
        )
        await state.set_state(st.barber.types)

    elif text == cf.get_text(lang, role, "button", "cabinet"):
        msg = get_cabinet_info(my_infos, lang)
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

    else:
        await show_error(message, state)


@router.message(st.barber.bookings)
async def show_bookings(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    date = cf.get_today(lang)
    my_infos = data.get("my_infos")
    bookings = await get_times_of_bookings(my_infos, date)

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    elif text == cf.get_text(lang, role, "button", "bookings_today"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "bookings_today_msg"),
            reply_markup=kb_r.br_bookings_today(lang, bookings)
        )
        await state.set_state(st.barber.bookings_today)

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
            await message.bot.send_message(
                user_id,
                cf.get_text(lang, role, "message", "bookings_otherday_next_msg"),
                reply_markup=kb_r.br_bookings_today(lang, bookings)
            ) 
            await state.set_state(st.barber.bookings_today)

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
        return

    handlers = {
        cf.get_text(lang, role, "button", "back"): {
            "message": cf.get_text(lang, role, "message", "main_menu_msg"),
            "keyboard": kb_r.br_main_menu(lang),
            "state": st.barber.main_menu
        },
        cf.get_text(lang, role, "button", "break_add"): {
            "message": cf.get_text(lang, role, "message", "break_add_reason_msg"),
            "keyboard": kb_r.back_main(lang),
            "state": st.barber.break_add_reason
        },
        cf.get_text(lang, role, "button", "break_edit"): {
            "message": cf.get_text(lang, role, "message", "break_edit_msg"),
            "keyboard": kb_r.back_main(lang),
            "state": st.barber.break_edit
        },
        cf.get_text(lang, role, "button", "break_delete"): {
            "message": cf.get_text(lang, role, "message", "break_delete_msg"),
            "keyboard": kb_r.back_main(lang),
            "state": st.barber.break_delete
        }
    }

    if text in handlers:
        handler = handlers[text]
        await message.bot.send_message(
            chat_id=user_id,
            text=handler["message"],
            reply_markup=handler["keyboard"]
        )
        await state.set_state(handler["state"])
        return

    await show_error(message, state)


@router.message(st.barber.break_add_reason)
async def add_break(message: Message, state: FSMContext):
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
        await state.set_state(st.barber.break_add_reason)

    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
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
                # день-месяц текущего года
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
    my_infos = data.get("my_infos")
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

        if text.isdigit():
            barber_break = await db.get_barber_break_by_id(text)

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
        break_data = data.get("break_data")
        start_time = BreaksRenderer._parse_iso(break_data.get("start_time"))

        try:
            h, m = map(int, text.split(":"))
            end_time = datetime.combine(start_time.date(), time(h, m)).replace(tzinfo=start_time.tzinfo)
            if end_time <= start_time:
                await show_error(message, state, "end_time_must_be_after_start_time_msg")
                return
        except Exception:
            await show_error(message, state, "invalid_time_format_msg")
            return

        break_data["end_time"] = end_time.isoformat()
        datas = { "end_time": end_time.isoformat() }
        await state.update_data(break_data=break_data)
        await db.update_barber_break_by_id(break_data.get("id"), data=datas)

        await message.bot.send_message(user_id, cf.get_text(lang, role, "message", "break_edit_success_msg"))
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "breaks_msg"),
            reply_markup=kb_r.br_breaks(lang)
        )
        await state.set_state(st.barber.breaks)


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

        if text.isdigit():
            barber_break = await db.get_barber_break_by_id(text)

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
                await show_error(message, state)

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


@router.message(st.barber.types)
async def show_types(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

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
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.type_add)

    elif text == cf.get_text(lang, role, "button", "type_delete"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "type_delete_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.type_delete)

    else:
        await show_error(message, state)


@router.message(st.barber.type_add)
async def add_type(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.br_main_menu(lang)
        )
        await state.set_state(st.barber.main_menu)

    else:
        await show_error(message, state)




@router.message(st.barber.cabinet)
async def show_cabinet(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

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

    else:
        await show_error(message, state)


@router.message(st.barber.cabinet_phone)
async def edit_phone(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=get_cabinet_info(my_infos, lang),
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
            text=get_cabinet_info(my_infos, lang),
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
            text=get_cabinet_info(my_infos, lang),
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
            text=get_cabinet_info(my_infos, lang),
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
            text=get_cabinet_info(my_infos, lang),
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
            text=get_cabinet_info(my_infos, lang),
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
            text=get_cabinet_info(my_infos, lang),
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

        datas = {"default_from_hour": from_hour,
                "default_to_hour": to_hour}

        my_infos["default_from_hour"] = from_hour
        my_infos["default_to_hour"] = to_hour

        await db.update_barber_by_id(my_infos.get("id"), datas)
        await message.bot.send_message(
            chat_id=user_id,
            text=get_cabinet_info(my_infos, lang),
            parse_mode="HTML",
            reply_markup=kb_r.br_cabinet(lang)
        )
        await state.set_state(st.barber.cabinet)