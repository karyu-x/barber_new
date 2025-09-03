import asyncio
import re
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from configs import functions as cf
from databases import database as db
from states import state as st
from keyboards import reply as kb_r
from keyboards import inline as kb_i

admin_router = Router()
router = admin_router

log = logging.getLogger(__name__)

role = "director"

# === Utils ===
DURATION_RE = re.compile(r"^(\d{1,2}:\d{2}|\d{1,3})$")

## parse price
def _parse_price(s: str) -> int | None:
    PRICE_RE = re.compile(r"\d+")
    digits = "".join(PRICE_RE.findall(s))
    if not digits:
        return None
    return int(digits)


## get user infos
async def get_user_context(entity, state):
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    user_id = entity.from_user.id

    if isinstance(entity, Message):
        text = (getattr(entity, "text", "") or "").strip()
        return user_id, data, lang, text
    
    if isinstance(entity, CallbackQuery):
        action = (getattr(entity, "data", "") or "").strip()
        return user_id, data, lang, action
        

## Navigate -> back, main
async def navigate_back_or_main(entity, state, target_state, target_text, target_markup, *args):
    user_id, _, lang, action = await get_user_context(entity, state)
    reply_markup = target_markup(lang, *args) if callable(target_markup) else target_markup

    if isinstance(target_text, str) and not target_text.startswith("<") and " " not in target_text:
        final_text = cf.get_text(lang, role, "message", target_text)
    else:
        final_text = target_text

    if isinstance(entity, CallbackQuery):
        if "back" in action or action == "back":
            if entity.message.text != final_text or entity.message.reply_markup != reply_markup:
                await entity.message.edit_text(final_text, parse_mode="HTML", reply_markup=reply_markup)
        else:  
            await entity.message.delete()
            await entity.bot.send_message(user_id, final_text, parse_mode="HTML", reply_markup=reply_markup)
        await entity.answer()

    elif isinstance(entity, Message):
        await entity.bot.send_message(user_id, final_text, parse_mode="HTML", reply_markup=reply_markup)

    await state.set_state(target_state)   


## Error
async def show_error(entity, state, error_key: str = "unknown_command"):
    user_id, _, lang, action = await get_user_context(entity, state)
    text = cf.get_text(lang, "errors", error_key)

    if isinstance(entity, CallbackQuery):
        await entity.answer(text, show_alert=True)
    else:  
        await entity.bot.send_message(chat_id=user_id, text=text)


## Booking info
async def get_booking_info(lang, booking):
    barber = booking.get("barber")
    client = booking.get("user")
    service = booking.get("service")
    start_time = booking.get("start_time")
    end_time = booking.get("end_time")
    status = booking.get("status")

    if isinstance(barber, int):
        barber = await db.get_user_by_id(id=barber)
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
        "barber": barber.get("first_name") if barber else "❌",
        "service": service.get("name") if service else "❌",
        "price": service.get("price") if service and service.get("price") else "❌",
        "start_time": fmt_time(start_time),
        "end_time": fmt_time(end_time),
        "status": status_map.get(status, status)
    }
    template = cf.get_text(lang, role, "message", "booking_info_msg")
    
    return template.format(**data)


## Barber card
def get_barber_card(lang, barber):
    barber_data = {
        "name": barber.get("first_name") or "❌",
        "phone_number": barber.get("phone_number") or "❌",
        "description": barber.get("description") or "❌",
        "rating": barber.get("rating") or "❌",
        "from_hour": barber.get("default_from_hour")[:5] if barber.get("default_from_hour") else "❌",
        "to_hour": barber.get("default_to_hour")[:5] if barber.get("default_to_hour") else "❌",
        "photo": "✅" if barber.get("photo") else "❌"
    }
    text_reply = cf.get_text(lang, role, "message", "barber_info_msg").format(**barber_data)
    return text_reply

async def send_barber_card(message, state, lang, barber):
    msg = get_barber_card(lang, barber)
    await message.bot.send_message(message.from_user.id, msg, parse_mode="HTML", reply_markup=kb_i.barber_detail(lang))
    await state.set_state(st.admin.barber_detail)


## get clients info
def get_clients_info(lang, clients):
    client_lines = []
    for s in clients:
        user_ban = 5 in (s.get("roles") or [])
        datas = {
            "first_name": s.get("first_name") or '❌',
            "phone_number": s.get("phone_number") or "❌",
            "language": '🇺🇿' if s.get('language') == 'uz' else '🇷🇺',
            "total_bookings": s.get("total_bookings") or 0,
            "status": "⛔️" if user_ban else "✅"
        }
        line = cf.get_text(lang, role, "message", "client_item_msg").format(**datas)
        client_lines.append(line)

    reply_text = cf.get_text(lang, role, "message", "client_last_list_msg")
    return f"{reply_text}\n\n" + "\n\n".join(client_lines)

def get_client_card(lang, client):
    user_ban = 5 in (client.get("roles") or [])
    datas = {
            "first_name": client.get("first_name") or '❌',
            "phone_number": client.get("phone_number") or "❌",
            "language": '🇺🇿' if client.get('language') == 'uz' else '🇷🇺',
            "total_bookings": client.get("total_bookings") or 0,
            "status": "⛔️" if user_ban else "✅"
        }
    reply_text = cf.get_text(lang, role, "message", "client_item_msg").format(**datas)
    return reply_text


## get services info
async def get_services_info(lang, role, type_id, type_name):
    filtered_services = await db.get_barber_services(type_id)
    if filtered_services:
        service_lines = [
            f"• <b>{s['name']}</b> — {s['price'] if s['price'] is not None else '❌'}\n"
            f"🕒 {s['duration'] if s['duration'] is not None else '❌'}\n"
            f"📝 {s['description'] if s['description'] is not None else '❌'}"
            for s in filtered_services
        ]
        services_text = "\n\n".join(service_lines)
    else:
        services_text = cf.get_text(lang, role, "message", "services_no_msg")

    reply_text = cf.get_text(lang, role, "message", "type_services_msg").format(type_name=type_name)
    return f"{reply_text}\n\n{services_text}"

async def get_service_info(lang, role, item: dict) -> str:
    body = cf.get_text(lang, role, "message", "service_detail_msg").format(
        description=item.get("description") or "-",
        duration=item.get("duration") or "-",
        price=f"{(item.get('price') or 0):,}"
    )
    return f"<b>{item['name']}</b>\n\n{body}"

##################################################################################################################

@router.message(st.admin.main_menu)
async def main_menu(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    my_infos = data.get("my_infos")

    button_keys = [
        "bookings", "notifications", "settings", "clients", "analytics", "user_menu"
    ]
    buttons = {cf.get_text(lang, role, "button", k): k for k in button_keys}
    admin_buttons = set(cf.get_admin_buttons(user_id) or [])

    async def send_menu(state_name, msg_key, reply_markup):
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", msg_key),
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        await state.set_state(state_name)

    handlers = {
        "bookings": lambda: send_menu(st.admin.bookings, "bookings_msg", kb_r.bookings(lang)),
        "notifications": lambda: send_menu(st.admin.notifications, "notifications_msg", kb_r.notifications(lang)),
        "settings": lambda: send_menu(st.admin.settings, "settings_msg", kb_i.settings(lang, "admin")),
        "clients": lambda: send_menu(st.admin.clients, "clients_msg", kb_i.clients(lang)),
        "analytics": lambda: send_menu(st.admin.analytics, "analytics_msg", kb_r.analytics(lang)),
        "user_menu": lambda: send_menu(st.user.main_menu, "main_menu_msg", kb_r.us_main_menu(lang, my_infos.get("roles")))
    }

    btn_key = buttons.get(text)
    if btn_key:
        if btn_key not in admin_buttons:
            await show_error(message, state, "no_access_button")
            return
        handler = handlers.get(btn_key)
        if handler:
            await handler()
            return

    await show_error(message, state)

##################################################################################################################

@router.message(st.admin.notifications)
async def notifications(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    t_input_text = cf.get_text(lang, role, "button", "input_text")
    t_input_photo = cf.get_text(lang, role, "button", "input_photo")
    t_input_button = cf.get_text(lang, role, "button", "input_button")
    t_check_post = cf.get_text(lang, role, "button", "check_post")
    t_back_main = cf.get_text(lang, role, "button", "back")

    async def handle_input_text():
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "input_text_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.input_text)

    async def handle_input_photo():
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "input_photo_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.input_photo)

    async def handle_input_button():
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "input_button_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.input_button)

    async def handle_check_post():
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "check_post_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.check_post(lang)
        )
        await state.set_state(st.admin.check_post)

    async def handle_back_main():
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.ad_main_menu(lang, user_id)
        )
        await state.set_state(st.admin.main_menu)

    handlers = {
        t_input_text: handle_input_text,
        t_input_photo: handle_input_photo,
        t_input_button: handle_input_button,
        t_check_post: handle_check_post,
        t_back_main: handle_back_main
    }
    handle = handlers.get(text)

    if handle:
        await handle()
        return

    await show_error(message, state)


@router.message(st.admin.input_text)
async def input_text(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": "notifications_msg",
            "reply_markup": kb_r.notifications(lang),
            "state": st.admin.notifications
        },
        cf.get_text(lang, role, "button", "back_main"): {
            "text": "main_menu_msg",
            "reply_markup": kb_r.ad_main_menu(lang, user_id),
            "state": st.admin.main_menu
        }
    }
    action = back_actions.get(text)

    if action:
        await navigate_back_or_main(message, state, action["state"], action["text"], action["reply_markup"])
        return

    reply_text = cf.get_text(lang, role, "message", "text_accepted_msg").format(text)
    await state.update_data(description=text)
    await message.bot.send_message(
        chat_id=user_id,
        text=reply_text,
        parse_mode="HTML",
        reply_markup=kb_r.notifications(lang)
    )
    await state.set_state(st.admin.notifications)


@router.message(st.admin.input_photo)
async def input_photo(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": "notifications_msg",
            "reply_markup": kb_r.notifications(lang),
            "state": st.admin.notifications
        },
        cf.get_text(lang, role, "button", "back_main"): {
            "text": "main_menu_msg",
            "reply_markup": kb_r.ad_main_menu(lang, user_id),
            "state": st.admin.main_menu
        }
    }
    action = back_actions.get(text)

    if action:
        await navigate_back_or_main(message, state, action["state"], action["text"], action["reply_markup"])
        return
    
    if message.photo:
        photo_id = message.photo[-1].file_id  
        await state.update_data(photo=photo_id)

        reply_text = cf.get_text(lang, role, "message", "photo_accepted_msg")
        await message.bot.send_photo(
            chat_id=user_id,
            photo=photo_id,
            caption=reply_text,
            reply_markup=kb_r.notifications(lang)
        )
        await state.set_state(st.admin.notifications)
        return

    await show_error(message, state, "photo_required_msg")


@router.message(st.admin.input_button)
async def input_button(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": "notifications_msg",
            "reply_markup": kb_r.notifications(lang),
            "state": st.admin.notifications
        },
        cf.get_text(lang, role, "button", "back_main"): {
            "text": "main_menu_msg",
            "reply_markup": kb_r.ad_main_menu(lang, user_id),
            "state": st.admin.main_menu
        }
    }
    action = back_actions.get(text)

    if action:
        await navigate_back_or_main(message, state, action["state"], action["text"], action["reply_markup"])
        return

    buttons = data.get("buttons", [])
    new_buttons = []
    lines = message.text.split("\n")
    for line in lines:
        if "-" not in line:
            continue
        text, url = map(str.strip, line.split("-", 1))
        if url.startswith(("http://", "https://")):
            new_buttons.append({"text": text, "url": url})
        else:
            continue

    if not new_buttons:
        await show_error(message, state, "invalid_button_format")
        return

    buttons.extend(new_buttons)
    await state.update_data(buttons=buttons)
    formatted = "\n".join([f"🔘 <b>{b['text']}</b> - {b['url']}" for b in buttons])
    title = cf.get_text(lang, role, "message", "button_list_title")
    await message.bot.send_message(
        chat_id=user_id,
        text=f"📋 <b>{title}</b>\n\n{formatted}",
        parse_mode="HTML",
        reply_markup=kb_r.notifications(lang)
    )
    await state.set_state(st.admin.notifications)


@router.message(st.admin.check_post)
async def check_post(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    text_back = cf.get_text(lang, role, "button", "back")
    text_back_main = cf.get_text(lang, role, "button", "back_main")
    text_preview = cf.get_text(lang, role, "button", "preview_post")
    text_confirm = cf.get_text(lang, role, "button", "confirm_post")

    async def handle_back():
        await navigate_back_or_main(message, state, st.admin.notifications, "notifications_msg", kb_r.notifications(lang))

    async def handle_back_main():
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))

    async def handle_preview():
        caption = data.get("description", "")
        photo = data.get("photo", "")
        buttons = data.get("buttons", [])
        markup = kb_i.post_button(buttons) if buttons else None

        if photo:
            await message.bot.send_photo(
                user_id,
                photo=photo,
                caption=caption,
                reply_markup=markup
            )
        elif caption:
            await message.bot.send_message(
                user_id,
                text=caption,
                reply_markup=markup
            )
        else:
            await message.bot.send_message(
                user_id,
                cf.get_text(lang, role, "message", "notification_not_found_msg")
            )

    async def handle_send():
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "confirm_post_msg"),
            reply_markup=kb_i.confirm_reject(lang)
        )
        await state.set_state(st.admin.confirm_post)

    handlers = {
        text_back: handle_back,
        text_back_main: handle_back_main,
        text_preview: handle_preview,
        text_confirm: handle_send
    }
    handler = handlers.get(text)

    if handler:
        await handler()
        return
    
    await show_error(message, state)


@router.callback_query(st.admin.confirm_post)
async def confirm_post(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    if action == "back":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "check_post_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.check_post(lang)
        )
        await state.set_state(st.admin.check_post)
        await call.answer()
        return

    if action == "main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        await call.answer()
        return
    
    if action == "confirm":
        description = data.get("description")
        photo = data.get("photo")
        buttons = data.get("buttons", [])
        reply_markup = kb_i.post_button(buttons) if buttons else None

        users = await db.get_users_all()
        total = len(users)
        sem = asyncio.Semaphore(20)
        success = 0
        failed = 0

        def progress_bar(done: int, total: int, length: int = 20) -> str:
            if total == 0:
                return ""
            filled = int(length * done / total)
            return "█" * filled + "░" * (length - filled)

        status_msg = await call.message.edit_text(
            f"📤 Начинаем рассылку...\n0 / {total}\n[░░░░░░░░░░░░░░░░░░░░]"
        )

        async def send_one(uid: int):
            nonlocal success, failed
            async with sem:
                try:
                    if photo:
                        await call.bot.send_photo(uid, photo, caption=description, reply_markup=reply_markup, parse_mode="HTML")
                    else:
                        await call.bot.send_message(uid, description, reply_markup=reply_markup, parse_mode="HTML")
                    success += 1
                except Exception as e:
                    failed += 1
                    log.warning("Broadcast fail uid=%s: %s", uid, e)

        CHUNK = 200
        for i in range(0, total, CHUNK):
            chunk = users[i:i+CHUNK]
            await asyncio.gather(*(send_one(u["telegram_id"]) for u in chunk))

            done = i + len(chunk)
            bar = progress_bar(done, total)
            await status_msg.edit_text(
                f"📊 Прогресс: {done} / {total}\n[{bar}]"
            )
            await asyncio.sleep(0.1)

        await state.update_data(description=None, photo=None, buttons=None)

        datas = { "success": success, "failed": failed }
        await status_msg.edit_text(cf.get_text(lang, role, "message", "post_sent_result").format(**datas), parse_mode="HTML")

        await call.bot.send_message(user_id, cf.get_text(lang, role, "message", "main_menu_msg"), parse_mode="HTML", reply_markup=kb_r.ad_main_menu(lang, user_id))
        await state.set_state(st.admin.main_menu)
        await call.answer()
        return

    await show_error(call, state)
##################################################################################################################

@router.message(st.admin.bookings)
async def bookings(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    t_back = cf.get_text(lang, role, "button", "back")
    t_today = cf.get_text(lang, role, "button", "bookings_today")
    t_otherday = cf.get_text(lang, role, "button", "bookings_otherday")
    t_cancel = cf.get_text(lang, role, "button", "bookings_cancel")
    t_forward = cf.get_text(lang, role, "button", "bookings_forward")

    async def handle_back():
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.ad_main_menu(lang, user_id)
        )
        await state.set_state(st.admin.main_menu)

    async def handle_books_today():
        today = cf.get_today(lang)
        await state.update_data(back_state=st.admin.bookings_today,
                                selected_day=today)
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "bookings_today_msg"),
            parse_mode="HTML",
            reply_markup=await kb_r.bookings_today(lang)
        )
        await state.set_state(st.admin.bookings_today)

    async def handle_books_otherday():
        await state.update_data(back_state=st.admin.bookings_otherday)
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "bookings_otherday_msg"),
            parse_mode="HTML",
            reply_markup=await kb_r.bookings_otherday(lang)
        )
        await state.set_state(st.admin.bookings_otherday)

    async def handle_books_cancel():
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "bookings_cancel_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.bookings_cancel)

    async def handle_books_forward():
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "bookings_forward_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.bookings_forward)
        
    handlers = {
        t_back: handle_back,
        t_today: handle_books_today,
        t_otherday: handle_books_otherday,
        t_cancel: handle_books_cancel,
        t_forward: handle_books_forward
    }
    handle = handlers.get(text)

    if handle:
        await handle()
        return
    
    await show_error(message, state)


@router.message(st.admin.bookings_today)
async def today_books(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    back_state = data.get("back_state")

    if text == cf.get_text(lang, role, "button", "back"):
        if back_state == st.admin.bookings_otherday:
            await navigate_back_or_main(message, state, st.admin.bookings_otherday, "bookings_otherday_msg", await kb_r.bookings_otherday(lang))
        else:
            await navigate_back_or_main(message, state, st.admin.bookings, "bookings_msg", kb_r.bookings(lang))
        return
    
    elif text == cf.get_text(lang, role, "button", "back_main"):
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    barbers = await db.get_barbers_all()
    for item in barbers:
        if text == item["first_name"]:
            await state.update_data(barber=item)
            await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
            date = data.get("selected_day")
            await message.bot.send_message(
                user_id,
                cf.get_text(lang, role, "message", "bookings_barber_msg").format(barber_name=item["first_name"]),
                parse_mode="HTML",
                reply_markup=await kb_i.bookings_barber(lang, item["id"], date.get("full_date"))
            )
            await state.set_state(st.admin.bookings_barber)
            return
    
    await show_error(message, state)


@router.message(st.admin.bookings_otherday)
async def other_day_books(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    if text == cf.get_text(lang, role, "button", "back"):
        await navigate_back_or_main(message, state, st.admin.bookings, "bookings_msg", kb_r.bookings(lang))
        return
    
    elif text == cf.get_text(lang, role, "button", "back_main"):
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    days = cf.get_days_from_today(lang)
    selected_day = None
    for day in days:
        if text == day.get("date"):
            await state.update_data(selected_day=day)
            selected_day = day
            break

    if selected_day:
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "bookings_otherday_next_msg"),
            reply_markup=await kb_r.bookings_today(lang)
        )
        await state.set_state(st.admin.bookings_today)
        return

    await show_error(message, state)


@router.callback_query(F.data.startswith("bron:"), st.admin.bookings_barber)
async def bookings_barber(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    if action == "bron:back":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "bookings_otherday_next_msg"),
            reply_markup=await kb_r.bookings_today(lang)
        )
        await state.set_state(st.admin.bookings_today)
        await call.answer()
        return

    if action == "bron:main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        await call.answer()
        return
    
    booking_id = action.split(":")[1]
    booking = await db.get_booking_by_id(booking_id)

    if booking:
        await state.update_data(booking=booking)
        msg = await get_booking_info(lang, booking)
        await call.message.edit_text(
            msg,
            parse_mode="HTML",
            reply_markup=await kb_i.booking_detail(lang, booking_id)
        )
        await state.set_state(st.admin.booking_detail)
        await call.answer()


@router.callback_query(F.data.startswith("booking_detail"), st.admin.booking_detail)
async def booking_detail(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    booking = data.get("booking")
    client = await db.get_user_by_id(id=booking["user"])

    a_back = "booking_detail:back"
    a_main = "booking_detail:main"
    a_reminder = "booking_detail:reminder"
    a_cancel = "booking_detail:cancel"
    a_forward = "booking_detail:forward"

    async def handle_back():
        date = data.get("selected_day")
        barber = data.get("barber")
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "bookings_barber_msg").format(barber_name=barber["first_name"]),
            reply_markup=await kb_i.bookings_barber(lang, barber.get("id"), date.get("full_date")),
            parse_mode="HTML"
        )
        await state.set_state(st.admin.bookings_barber)

    async def handle_main():
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))

    async def handle_reminder():
        day = booking["start_time"].split("T")[0]
        time = booking["start_time"].split("T")[1][:5]
        start_time = f"{day} {time}"
        await call.answer(cf.get_text(lang, role, "message", "booking_reminder_sent_msg"), show_alert=True)
        await call.bot.send_message(
            client.get("telegram_id"),
            cf.get_text(lang, role, "message", "booking_reminder_msg").format(start_time),
            parse_mode="HTML"
        )

    async def handle_cancel():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "booking_cancel_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.booking_cancel)

    async def handle_forward():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "booking_forward_msg"),
            parse_mode="HTML",
            reply_markup=await kb_i.services_prices(lang)
        )
        await state.set_state(st.admin.booking_forward)

    handlers = {
        a_back: handle_back,
        a_main: handle_main,
        a_reminder: handle_reminder,
        a_cancel: handle_cancel,
        a_forward: handle_forward
    }
    handle = handlers.get(action)

    if handle:
        await handle()
        await call.answer()
        return

    await show_error(call, state)


@router.message(st.admin.booking_cancel)
async def cancel_books(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    booking = data.get("booking")

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        msg = await get_booking_info(lang, booking)
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await navigate_back_or_main(message, state, st.admin.booking_detail, msg, await kb_i.booking_detail(lang, booking.get("id")))
        return
    
    if text == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if not data.get("cancel_reason"):
        await state.update_data(cancel_reason=text)
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "booking_cancel_confirm_msg").format(reason=text),
            parse_mode="HTML",
            reply_markup=kb_i.confirm_reject(lang)
        )
        await state.set_state(st.admin.booking_cancel_confirm)
        return

    await show_error(message, state)


@router.callback_query(st.admin.booking_cancel_confirm)
async def cancel_books_confirm(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    cancel_state = data.get("cancel_state")
    reason = data.get("cancel_reason", "")
    booking = data.get("booking")
    date = data.get("selected_day")
    barber = data.get("barber")

    if action == "back":
        if cancel_state == "bookings_cancel":
            await call.message.delete()
            await call.bot.send_message(
                user_id,
                cf.get_text(lang, role, 'message', 'booking_cancel_msg'),
                reply_markup=kb_r.back_main(lang)
            )
            await state.set_state(st.admin.bookings_cancel)
            await state.update_data(cancel_reason=None)
            await call.answer()
            return

        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "booking_cancel_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.booking_cancel)
        await call.answer()
        return

    if action == "main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        await state.update_data(
            booking=None,
            barber=None,
            selected_day=None,
            cancel_state=None,
            cancel_reason=None,
            cancel_client_phone=None
        )
        await call.answer()
        return

    if action == "confirm":
        if booking:
            await db.booking_cancel_by_id(booking["id"], user_id, reason)

            await call.message.edit_text(
                cf.get_text(lang, role, "message", "booking_cancelled_success_msg").format(reason=reason),
                parse_mode="HTML",
                reply_markup=None
            )

        if cancel_state == "bookings_cancel":
            await call.bot.send_message(
                user_id,
                cf.get_text(lang, role, 'message', 'bookings_msg'),
                parse_mode="HTML",
                reply_markup=kb_r.bookings(lang)
            )
            await state.set_state(st.admin.bookings)
            await state.update_data(
                booking=None,
                cancel_state=None,
                cancel_reason=None,
                cancel_client_phone=None
            )
            await call.answer()
            return
        
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "bookings_barber_msg").format(barber_name=barber["first_name"]),
            parse_mode="HTML",
            reply_markup=await kb_i.bookings_barber(lang, barber.get("id"), date.get("full_date"))
        )
        await state.update_data(cancel_reason=None,
                                cancel_client_phone=None,
                                booking=None)
        await state.set_state(st.admin.bookings_barber)
        await call.answer()
        return

    await show_error(call, state)


@router.callback_query(st.admin.booking_forward)
async def reschedule_books(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)
    booking = data.get("booking")
    forward_state = data.get("forward_state")

    if action == "services_btn:back":

        if forward_state == "bookings_forward":
            await call.message.delete()
            await call.bot.send_message(
                user_id,
                cf.get_text(lang, role, "message", "bookings_forward_msg"),
                parse_mode="HTML",
                reply_markup=kb_r.back_main(lang)
            )
            await state.set_state(st.admin.bookings_forward)
            await state.update_data(
                booking=None,
                forward_state=None,
                forward_client_phone=None
            )
            await call.answer()
            return

        msg = await get_booking_info(lang, booking)
        await cf.get_random_modes(call, user_id, kb_r.ReplyKeyboardRemove)
        await navigate_back_or_main(call, state, st.admin.booking_detail, msg, await kb_i.booking_detail(lang, booking.get("id")))
        return

    if action == "services_btn:main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        await state.update_data(
            booking=None,
            forward_state=None,
            forward_client_phone=None
        )
        return
    
    tg_id = action.split(":")[1]
    barber = await db.get_user_by_id(telegram_id=tg_id)

    if not barber:
        await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)
        return

    await state.update_data(barber=barber)
    await call.message.edit_text(
        cf.get_text(lang, role, "message", "booking_forward_confirm_msg").format(barber=barber.get("first_name")),
        parse_mode="HTML",
        reply_markup=kb_i.confirm_reject(lang)
    )
    await state.set_state(st.admin.booking_forward_confirm)
    await call.answer()


@router.callback_query(st.admin.booking_forward_confirm)
async def booking_forward_confirm(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    booking = data.get("booking")
    barber = data.get("barber")
    date = data.get("selected_day")
    forward_state = data.get("forward_state")

    if action == "back":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "booking_forward_msg"),
            parse_mode="HTML",
            reply_markup=await kb_i.services_prices(lang)
        )
        await state.set_state(st.admin.booking_forward)
        await call.answer()
        return

    if action == "main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        await state.update_data(
            booking=None,
            barber=None,
            selected_day=None,
            forward_state=None,
            forward_client_phone=None
        )
        await call.answer()
        return

    if action == "confirm":
        if booking and barber:
            await db.booking_forward_by_id(booking["id"], barber["id"])
            await call.answer(cf.get_text(lang, role, "message", "booking_forwarded_success_msg"), show_alert=True)

            if forward_state == "bookings_forward":
                await call.message.delete()
                await call.bot.send_message(
                    user_id,
                    cf.get_text(lang, role, "message", "bookings_msg"),
                    parse_mode="HTML",
                    reply_markup=kb_r.bookings(lang)
                )
                await state.set_state(st.admin.bookings)
                await call.answer()
                return

            await call.bot.send_message(
                user_id,
                cf.get_text(lang, role, "message", "bookings_barber_msg").format(barber_name=barber["first_name"]),
                reply_markup=await kb_i.bookings_barber(lang, barber.get("id"), date.get("full_date")),
                parse_mode="HTML"
            )
            await state.set_state(st.admin.bookings_barber)
            await call.answer()
            return

    await show_error(call, state)


@router.message(st.admin.bookings_cancel)
async def bookings_cancel(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        await navigate_back_or_main(message, state, st.admin.bookings, "bookings_msg", kb_r.bookings(lang))
        return

    if text == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if not data.get("cancel_client_phone"):
        phone = re.sub(r"[^\d+]", "", text)
        if not re.fullmatch(r"\+?998\d{9}", phone):
            return await show_error(message, state, "invalid_phone_number_msg")

        booking = await db.get_active_booking_by_client_phone(phone)
        if not booking:
            return await message.answer(cf.get_text(lang, role, "message", "booking_not_found_msg"))

        await state.update_data(cancel_client_phone=phone, booking=booking)
        booking_info = await get_booking_info(lang, booking)
        await message.answer(
            f"{booking_info}\n\n{cf.get_text(lang, role, 'message', 'booking_cancel_msg')}",
            parse_mode="HTML",
        )
        return
    
    if not data.get("cancel_reason"):
        await state.update_data(cancel_reason=text)
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await message.answer(
            cf.get_text(lang, role, "message", "booking_cancel_confirm_msg").format(reason=text),
            parse_mode="HTML",
            reply_markup=kb_i.confirm_reject(lang),
        )
        await state.update_data(cancel_state="bookings_cancel")
        await state.set_state(st.admin.booking_cancel_confirm)
        return

    await show_error(message, state)


@router.message(st.admin.bookings_forward)
async def bookings_forward(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        await navigate_back_or_main(message, state, st.admin.bookings, "bookings_msg", kb_r.bookings(lang))
        return
    
    if text == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if not data.get("forward_client_phone"):
        phone = re.sub(r"[^\d+]", "", text)
        if not re.fullmatch(r"\+?998\d{9}", phone):
            return await show_error(message, state, "invalid_phone_number_msg")

        booking = await db.get_active_booking_by_client_phone(phone)
        if not booking:
            return await message.answer(cf.get_text(lang, role, "message", "booking_not_found_msg"))

        await state.update_data(forward_client_phone=phone, booking=booking)
        booking_info = await get_booking_info(lang, booking)
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await message.answer(
            f"{booking_info}\n\n{cf.get_text(lang, role, 'message', 'booking_forward_msg')}",
            parse_mode="HTML",
            reply_markup=await kb_i.services_prices(lang)
        )
        await state.update_data(forward_state="bookings_forward")
        await state.set_state(st.admin.booking_forward)
        return

    await show_error(message, state)

#################################################### SETTINGS MENU ##############################################################

@router.callback_query(F.data.startswith("setting_btn:"), st.admin.settings)
async def settings(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    t_services = "setting_btn:services_prices"
    t_barbers = "setting_btn:barbers"
    t_admins = "setting_btn:admins"
    t_language = "setting_btn:language"
    t_back = "setting_btn:back"

    async def services():
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "services_prices_msg"),
            parse_mode="HTML",
            reply_markup=await kb_i.services_prices(lang)
        )
        await state.set_state(st.admin.services_menu)

    async def barbers():
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "barbers_msg"),
            parse_mode="HTML",
            reply_markup=await kb_i.barbers(lang)
        )
        await state.set_state(st.admin.barbers)

    async def admins():
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "admins_msg"),
            parse_mode="HTML",
            reply_markup=await kb_i.admins(lang)
        )
        await state.set_state(st.admin.admins)

    async def language():
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "language_msg"),
            parse_mode="HTML",
            reply_markup=kb_i.language(lang)
        )
        await state.set_state(st.admin.language)

    async def back():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.ad_main_menu(lang, user_id)
        )
        await state.set_state(st.admin.main_menu)

    handlers = {
        t_services: services,
        t_barbers: barbers,
        t_admins: admins,
        t_language: language,
        t_back: back
    }
    handle = handlers.get(action)

    if handle:
        await handle()
        await call.answer()
        return
        
    await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)

########################################################## SERVICE & PRICE ##########################################################

@router.callback_query(F.data.startswith("services_btn:"), st.admin.services_menu)
async def services_prices(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    if action == "services_btn:back":
        await navigate_back_or_main(call, state, st.admin.settings, "settings_msg", kb_i.settings(lang, "admin"))
        return
    
    if action == "services_btn:main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    parts = action.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        barber_telegram_id = int(parts[1])
        barber = await db.get_user_by_id(telegram_id=barber_telegram_id)
        if not barber:
            await call.answer(cf.get_text(lang, role, "message", "barber_not_found_msg"), show_alert=True)
            return

        await state.update_data(
            barber_id=barber["id"],
            barber_tg_id=barber_telegram_id,
            barber_name=barber["first_name"]
        )

        barber_types = await db.get_barber_types(barber_telegram_id)
        if barber_types:
            await call.message.edit_text(
                cf.get_text(lang, role, "message", "barber_types_msg").format(barber=barber["first_name"]),
                parse_mode="HTML",
                reply_markup=await kb_i.barber_types(lang, barber_telegram_id)
            )
        else:
            await call.message.edit_text(
                cf.get_text(lang, role, "message", "barber_types_no_msg"),
                reply_markup=await kb_i.barber_types(lang, barber_telegram_id)
            )

        await state.set_state(st.admin.barber_types)
        await call.answer()
        return




@router.callback_query(F.data.startswith("types_btn:"), st.admin.barber_types)
async def barber_types(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)
    barber_telegram_id = data.get("barber_tg_id")

    if action == "types_btn:back":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "services_prices_msg"),
            parse_mode="HTML",
            reply_markup=await kb_i.services_prices(lang)
        )
        await state.set_state(st.admin.services_menu)
        await call.answer()
        return
    
    if action == "types_btn:main":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.ad_main_menu(lang, user_id)
        )
        await state.set_state(st.admin.main_menu)
        await call.answer()
        return

    if action == "types_btn:add":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "type_add_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.type_add)
        await call.answer()
        return

    parts = action.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        type_id = int(parts[1])
        service_type = await db.get_barber_type_by_id(type_id)
        if not service_type:
            await call.answer(cf.get_text(lang, role, "message", "type_not_found_msg"), show_alert=True)
            return

        await state.update_data(
            service_type_id=type_id,
            service_type_name=service_type["name"]
        )

        services_text = await get_services_info(lang, role, type_id, service_type["name"])

        await call.message.edit_text(
            services_text,
            parse_mode="HTML",
            reply_markup=await kb_i.barber_services(lang, type_id)
        )
        await state.set_state(st.admin.type_services)
        await call.answer()
        return


@router.message(st.admin.type_add)
async def add_type(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    barber_id = data.get("barber_id")
    barber_telegram_id = data.get("barber_tg_id")
    barber_name = data.get("barber_name")

    back = cf.get_text(lang, role, "button", "back")
    main = cf.get_text(lang, role, "button", "back_main")
    
    if text == back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barber_types_msg").format(barber=barber_name),
            parse_mode="HTML",
            reply_markup=await kb_i.barber_types(lang, barber_telegram_id)
        )
        await state.set_state(st.admin.barber_types)
        return
    
    if text == main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    datas = {"barber": barber_id, "name": text.strip()}

    await db.create_barber_type(datas)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "type_add_succes_msg").format(service_name=text),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await message.bot.send_message(
        user_id,
        cf.get_text(lang, role, "message", "barber_types_msg").format(barber=barber_name),
        parse_mode="HTML",
        reply_markup=await kb_i.barber_types(lang, barber_telegram_id)
    )
    await state.set_state(st.admin.barber_types)


@router.callback_query(st.admin.type_delete)
async def delete_type(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    barber_telegram_id = data.get("barber_tg_id")
    barber_name = data.get("barber_name") 
    type_name = data.get("service_type_name")
    type_id = data.get("service_type_id")

    if action == "back":
        services_text = await get_services_info(lang, role, type_id, type_name)
        await call.message.edit_text(
            services_text,
            parse_mode="HTML",
            reply_markup=await kb_i.barber_services(lang, type_id)
        )
        await state.set_state(st.admin.type_services)
        await call.answer()
        return

    if action == "main":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.ad_main_menu(lang, user_id)
        )
        await state.set_state(st.admin.main_menu)
        await call.answer()
        return

    if action == "confirm":
        await db.delete_barber_type_by_id(type_id)
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "type_delete_success_msg").format(type_name=type_name),
            reply_markup=None
        )
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barber_types_msg").format(barber=barber_name),
            parse_mode="HTML",
            reply_markup=await kb_i.barber_types(lang, barber_telegram_id)
        )
        await state.set_state(st.admin.barber_types)
        await call.answer()
        return

    await show_error(call, state)   


@router.callback_query(F.data.startswith("service_btn:"), st.admin.type_services)
async def barber_services(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    barber_telegram_id = data.get("barber_tg_id")
    barber_name = data.get("barber_name")
    type_id = data.get("service_type_id")

    if action == "service_btn:back":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "barber_types_msg").format(barber=barber_name or ""),
            parse_mode="HTML",
            reply_markup=await kb_i.barber_types(lang, barber_telegram_id)
        )
        await state.set_state(st.admin.barber_types)
        await call.answer()
        return

    if action == "service_btn:main":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.ad_main_menu(lang, user_id)
        )
        await state.set_state(st.admin.main_menu)
        await call.answer()
        return

    if action == "service_btn:delete":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "type_delete_msg"),
            parse_mode="HTML",
            reply_markup=kb_i.confirm_reject(lang)
        )
        await state.set_state(st.admin.type_delete)
        await call.answer()
        return

    if action == "service_btn:add":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "service_add_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.service_add)
        await call.answer()
        return

    parts = action.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        service_id = int(parts[1])

        item = await db.get_barber_service_by_id(service_id)
        if not item:
            await call.answer(cf.get_text(lang, role, "message", "service_not_found_msg"), show_alert=True)
            return

        await state.update_data(service_id=service_id, service_name=item["name"])
        detail_body = cf.get_text(lang, role, "message", "service_detail_msg").format(
            description=item.get("description") or "-",
            duration=item.get("duration") or "-",
            price=f"{(item.get('price') or 0):,}"
        )

        await call.message.edit_text(
            f"<b>{item['name']}</b>\n\n{detail_body}",
            parse_mode="HTML",
            reply_markup=kb_i.service_detail(lang)
        )
        await state.set_state(st.admin.service_detail)
        await call.answer()
        return

    await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)


@router.message(st.admin.service_add)
async def add_service(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    type_id = data.get("service_type_id")
    type_name =  data.get("service_type_name")

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if text == text_back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        services_text = await get_services_info(lang, role, type_id, type_name)
        await message.bot.send_message(
            user_id,
            services_text,
            parse_mode="HTML",
            reply_markup=await kb_i.barber_services(lang, type_id)
        )
        await state.set_state(st.admin.type_services)
        return

    datas = {"name": text, "service_type": type_id}
    await db.create_barber_service(datas)

    services_text = await get_services_info(lang, role, type_id, type_name)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "service_add_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await message.bot.send_message(
        user_id,
        services_text,
        parse_mode="HTML",
        reply_markup=await kb_i.barber_services(lang, type_id)
    )
    await state.set_state(st.admin.type_services)


@router.callback_query(st.admin.service_delete)
async def delete_service(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    type_id = data.get("service_type_id")
    service_id = data.get("service_id")
    type_name = data.get("service_type_name")

    if action == "confirm":
        await db.delete_barber_service_by_id(service_id)
        services_text = await get_services_info(lang, role, type_id, type_name)

        await call.message.edit_text(
            cf.get_text(lang, role, "message", "service_delete_success_msg"),
            reply_markup=None
        )
        await call.bot.send_message(
            user_id,
            services_text,
            parse_mode="HTML",
            reply_markup=await kb_i.barber_services(lang, type_id)
        )
        await state.set_state(st.admin.type_services)
        await call.answer()
        return

    if action == "back":
        item = await db.get_barber_service_by_id(service_id)
        detail_body = cf.get_text(lang, role, "message", "service_detail_msg").format(
            description=item.get("description") or "-",
            duration=item.get("duration") or "-",
            price=f"{(item.get('price') or 0):,}"
        )
        await call.message.edit_text(
            f"<b>{item['name']}</b>\n\n{detail_body}",
            parse_mode="HTML",
            reply_markup=kb_i.service_detail(lang)
        )
        await state.set_state(st.admin.service_detail)
        await call.answer()
        return

    if action == "main":
        await call.message.delete()
        await call.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.ad_main_menu(lang, user_id),
        )
        await call.answer()
        await state.set_state(st.admin.main_menu)
        return
    
    await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)


@router.callback_query(F.data.startswith("ser_detail_btn:"), st.admin.service_detail)
async def service_detail(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    type_id = data.get("service_type_id")
    type_name = data.get("service_type_name")
    service_id = data.get("service_id")

    async def handle_name():
        await call.message.delete()
        await call.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_edit_name_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.service_edit_name)

    async def handle_description():
        await call.message.delete()
        await call.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_edit_description_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.service_edit_description)

    async def handle_duration():
        await call.message.delete()
        await call.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_edit_duration_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.service_edit_duration)

    async def handle_price():
        await call.message.delete()
        await call.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_edit_price_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.service_edit_price)

    async def handle_back():
        services_text = await get_services_info(lang, role, type_id, type_name)
        await call.message.edit_text(
            services_text,
            parse_mode="HTML",
            reply_markup=await kb_i.barber_services(lang, type_id)
        )
        await state.set_state(st.admin.type_services)

    async def handle_main():
        await call.message.delete()
        await call.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.ad_main_menu(lang, user_id)
        )
        await state.set_state(st.admin.main_menu)

    async def handle_delete():
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "service_delete_msg"),
            reply_markup=kb_i.confirm_reject(lang)
        )
        await state.set_state(st.admin.service_delete)

    handlers = {
        "ser_detail_btn:back": handle_back,
        "ser_detail_btn:main": handle_main,
        "ser_detail_btn:delete": handle_delete,
        "ser_detail_btn:name": handle_name,
        "ser_detail_btn:description": handle_description,
        "ser_detail_btn:duration": handle_duration,
        "ser_detail_btn:price": handle_price
    }

    handle = handlers.get(action)
    if handle:
        await handle()
        await call.answer()
        return

    await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)


@router.message(st.admin.service_edit_name)
async def edit_service_name(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    type_id = data.get("service_type_id")
    service_id = data.get("service_id")

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        item = await db.get_barber_service_by_id(service_id)
        service_info = await get_service_info(lang, role, item)
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await navigate_back_or_main(message, state, st.admin.service_detail, service_info, kb_i.service_detail(lang))
        return

    if text == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    await db.update_barber_service_by_id(service_id, data={"name": text.strip()})

    item = await db.get_barber_service_by_id(service_id)
    service_info = await get_service_info(lang, role, item)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "service_edit_name_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await message.bot.send_message(
        user_id,
        service_info,
        parse_mode="HTML",
        reply_markup=kb_i.service_detail(lang)
    )
    await state.set_state(st.admin.service_detail)


@router.message(st.admin.service_edit_description)
async def edit_service_description(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    
    type_id = data.get("service_type_id")
    service_id = data.get("service_id")

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        item = await db.get_barber_service_by_id(service_id)
        service_info = await get_service_info(lang, role, item)
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await navigate_back_or_main(message, state, st.admin.service_detail, service_info, kb_i.service_detail(lang))
        return

    if text == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return
    
    await db.update_barber_service_by_id(service_id, data={"description": text.strip()})

    item = await db.get_barber_service_by_id(service_id)
    service_info = await get_service_info(lang, role, item)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "service_edit_description_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await message.bot.send_message(
        user_id,
        service_info,
        parse_mode="HTML",
        reply_markup=kb_i.service_detail(lang)
    )
    await state.set_state(st.admin.service_detail)


@router.message(st.admin.service_edit_duration)
async def edit_service_duration(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)    

    type_id = data.get("service_type_id")
    service_id = data.get("service_id")

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        item = await db.get_barber_service_by_id(service_id)
        service_info = await get_service_info(lang, role, item)
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await navigate_back_or_main(message, state, st.admin.service_detail, service_info, kb_i.service_detail(lang))
        return

    if text == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if not DURATION_RE.match(text):
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, "errors", "invalid_duration_msg"),
            parse_mode="HTML"
        )
        return

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
    await db.update_barber_service_by_id(service_id, data={"duration": duration_str})

    item = await db.get_barber_service_by_id(service_id)
    service_info = await get_service_info(lang, role, item)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "service_edit_duration_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await message.bot.send_message(
        user_id,
        service_info,
        parse_mode="HTML",
        reply_markup=kb_i.service_detail(lang)
    )
    await state.set_state(st.admin.service_detail)


@router.message(st.admin.service_edit_price)
async def edit_service_price(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    type_id = data.get("service_type_id")
    service_id = data.get("service_id")

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        item = await db.get_barber_service_by_id(service_id)
        service_info = await get_service_info(lang, role, item)
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await navigate_back_or_main(message, state, st.admin.service_detail, service_info, kb_i.service_detail(lang))
        return

    if text == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return
    
    price = _parse_price(text)
    if not price or price <= 0:
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, "errors", "invalid_price_msg"),
            parse_mode="HTML"
        )
        return
    
    await db.update_barber_service_by_id(service_id, data={"price": price})
    
    item = await db.get_barber_service_by_id(service_id)
    service_info = await get_service_info(lang, role, item)
    await message.bot.send_message(
        user_id,
        cf.get_text(lang, role, "message", "service_edit_price_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await message.bot.send_message(
        user_id,
        service_info,
        parse_mode="HTML",
        reply_markup=kb_i.service_detail(lang)
    )
    await state.set_state(st.admin.service_detail)

##################################################### SERVICE & PRICE #######################################################

########################################################## BARBERS ##########################################################

@router.callback_query(F.data.startswith("barber_btn:"), st.admin.barbers)
async def barbers(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    if action == "barber_btn:back":
        await navigate_back_or_main(call, state, st.admin.settings, "settings_msg", kb_i.settings(lang, "admin"))
        return
    
    if action == "barber_btn:main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if action == "barber_btn:add":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barber_add_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.barber_add)
        await call.answer()
        return

    parts = action.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        barber_id = int(parts[1])
        barber = await db.get_user_by_id(telegram_id=int(barber_id))
        rating = await db.get_barber_rating_by_id(int(barber_id))
        if not barber:
            await call.answer(cf.get_text(lang, role, "message", "barber_not_found_msg"), show_alert=True)
            return
        
        barber_data = {
            "name": barber["first_name"] or "❌",
            "phone_number": barber["phone_number"] or "❌",
            "description": barber["description"] or "❌",
            "rating": rating or "❌",
            "from_hour": barber["default_from_hour"][:5] if barber["default_from_hour"] else "❌",
            "to_hour": barber["default_to_hour"][:5] if barber["default_to_hour"] else "❌",
            "photo": "✅" if barber["photo"] else "❌"
        }

        text_reply = cf.get_text(lang, role, "message", "barber_info_msg").format(**barber_data)
        await state.update_data(
            barber_id=barber.get("id"),
            barber_tg_id=barber_id, 
            barber_name=barber["first_name"])
        await call.message.edit_text(
            text_reply,
            parse_mode="HTML",
            reply_markup=kb_i.barber_detail(lang)
        )

        await state.set_state(st.admin.barber_detail)
        await call.answer()
        return
    
    await show_error(call, state)
    

@router.message(st.admin.barber_add)
async def add_barber(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    t_back = cf.get_text(lang, role, "button", "back")
    t_main = cf.get_text(lang, role, "button", "back_main")

    if text == t_back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barbers_msg"),
            parse_mode="HTML",
            reply_markup=await kb_i.barbers(lang)
        )
        await state.set_state(st.admin.barbers)
        return

    if text == t_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    phone = text.replace(" ", "").replace("-", "")
    if not re.fullmatch(r"(\+?998\d{9})", phone):
        await show_error(message, state, "invalid_phone_number_msg")
        return

    await db.create_barber_by_phone(phone)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "barber_add_success_msg").format(phone=phone)
    )
    await message.bot.send_message(
        user_id,
        cf.get_text(lang, role, "message", "barbers_msg"),
        parse_mode="HTML",
        reply_markup=await kb_i.barbers(lang)
    )
    await state.set_state(st.admin.barbers)


@router.callback_query(F.data.startswith("bar_detail_btn:"), st.admin.barber_detail)
async def barber_detail(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    barber_name = data.get("barber_name")

    async def go_back():
        await navigate_back_or_main(call, state, st.admin.barbers, "barbers_msg", await kb_i.barbers(lang))

    async def go_main():
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))

    async def barber_delete():
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "barber_delete_msg").format(barber_name=barber_name),
            parse_mode="HTML",
            reply_markup=kb_i.confirm_reject(lang)
        )
        await state.set_state(st.admin.barber_delete)

    async def phone_edit():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barber_edit_phone_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.barber_edit_phone)

    async def description_edit():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barber_edit_description_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.barber_edit_description)

    async def photo_edit():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barber_edit_photo_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.barber_edit_photo)

    async def time_edit():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barber_edit_time_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.barber_edit_time)

    handlers = {
        "bar_detail_btn:back": go_back,
        "bar_detail_btn:main": go_main,
        "bar_detail_btn:delete": barber_delete,
        "bar_detail_btn:phone": phone_edit,
        "bar_detail_btn:description": description_edit,
        "bar_detail_btn:photo": photo_edit,
        "bar_detail_btn:time": time_edit,
    }

    handler = handlers.get(action)
    if handler:
        await handler()
        await call.answer()
        return
    
    await show_error(call, state)


@router.message(st.admin.barber_edit_phone)
async def edit_barber_phone(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    barber_id = data.get("barber_id")
    barber_telegram_id = data.get("barber_tg_id")

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if text == text_back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        barber = await db.get_user_by_id(telegram_id=barber_telegram_id)
        await send_barber_card(message, state, lang, barber)
        return
    
    phone = text.replace(" ", "").replace("-", "")
    if not re.match(r"^\+?998\d{9}$", phone):
        await show_error(message, state, "invalid_phone_number_msg")
        return

    datas = {"phone_number": phone}
    await db.update_barber_by_id(barber_id, datas)

    barber = await db.get_user_by_id(telegram_id=barber_telegram_id)
    await message.bot.send_message(
        user_id,
        cf.get_text(lang, role, "message", "barber_edit_phone_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await send_barber_card(message, state, lang, barber)


@router.message(st.admin.barber_edit_description)
async def edit_barber_description(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    barber_id = data.get("barber_id")
    barber_telegram_id = data.get("barber_tg_id")

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if text == text_back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        barber = await db.get_user_by_id(telegram_id=barber_telegram_id)
        await send_barber_card(message, state, lang, barber)
        return

    datas = {"description": text}
    await db.update_barber_by_id(barber_id, datas)
    
    barber = await db.get_user_by_id(telegram_id=barber_telegram_id)
    await message.bot.send_message(
        user_id,
        cf.get_text(lang, role, "message", "barber_edit_description_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await send_barber_card(message, state, lang, barber)


@router.message(st.admin.barber_edit_photo)
async def edit_barber_photo(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    barber_id = data.get("barber_id")
    barber_telegram_id = data.get("barber_tg_id")

    text_main = cf.get_text(lang, role, "button", "back_main")
    text_back = cf.get_text(lang, role, "button", "back")

    if message.text and message.text.strip() == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if message.text and message.text.strip() == text_back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        barber = await db.get_user_by_id(telegram_id=barber_telegram_id)
        await send_barber_card(message, state, lang, barber)
        return

    if not message.photo:
        await show_error(message, state, "photo_required_msg")
        return

    photo_id = message.photo[-1].file_id
    datas = {"photo": photo_id}
    await db.update_barber_by_id(barber_id, datas)

    barber = await db.get_user_by_id(telegram_id=barber_telegram_id)
    await message.bot.send_message(
        user_id,
        cf.get_text(lang, role, "message", "barber_edit_photo_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await send_barber_card(message, state, lang, barber)


@router.message(st.admin.barber_edit_time)
async def edit_barber_time(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    barber_id = data.get("barber_id")
    barber_telegram_id = data.get("barber_tg_id")

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if text == text_back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        barber = await db.get_user_by_id(telegram_id=barber_telegram_id)
        await send_barber_card(message, state, lang, barber)
        return

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
    await db.update_working_hours_by_id(barber_id, datas)

    barber = await db.get_user_by_id(telegram_id=barber_telegram_id)
    await message.bot.send_message(
        user_id,
        cf.get_text(lang, role, "message", "barber_edit_time_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await send_barber_card(message, state, lang, barber)


@router.callback_query(st.admin.barber_delete)
async def delete_barber(call: CallbackQuery, state:FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    barber_telegram_id = data.get("barber_tg_id")

    barber = await db.get_user_by_id(telegram_id=barber_telegram_id)

    if action == "back":
        msg = get_barber_card(lang, barber)
        await navigate_back_or_main(call, state, st.admin.barber_detail, msg, kb_i.barber_detail(lang))
        return

    if action == "main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if action == "confirm":
        await db.delete_barber_by_phone(barber.get("phone_number"))
        await call.message.edit_text(
            text=cf.get_text(lang, role, "message", "barber_delete_success_msg"),
            reply_markup=None
        )
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barbers_msg"),
            parse_mode="HTML",
            reply_markup=await kb_i.barbers(lang)
        )
        await state.set_state(st.admin.barbers)
        await call.answer()
        return

########################################################## ADMINS ##########################################################

@router.callback_query(F.data.startswith("admin_btn:"), st.admin.admins)
async def admins(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    if action == "admin_btn:back":
        await navigate_back_or_main(call, state, st.admin.settings, "settings_msg", kb_i.settings(lang, "admin"))
        return
    
    if action == "admin_btn:main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if action == "admin_btn:add":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "admin_add_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.admin_add)
        await call.answer()
        return
    
    parts = action.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        admin_id = int(parts[1])
        
        admin = await db.get_user_by_id(telegram_id=admin_id)
        if not admin:
            await call.answer(cf.get_text(lang, role, "message", "admin_not_found_msg"), show_alert=True)
            return

        await state.update_data(admin_id=admin.get("id"),
                                admin_tg_id=admin_id,
                                admin_name=admin.get("first_name"),
                                admin_phone=admin.get("phone_number"))

        button_ids = cf.get_admin_buttons(admin_id) or []
        but_names = [cf.button_title(lang, role, bid) for bid in button_ids]
        buttons_str = ", ".join(but_names) if but_names else "—"

        msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
            name=admin.get("first_name") or "",
            phone=admin.get("phone_number") or "",
            buttons=buttons_str
        )
        
        await call.message.edit_text(
            msg,
            parse_mode="HTML",
            reply_markup=kb_i.admin_detail(lang)
        )
        
        await state.set_state(st.admin.admin_detail)
        await call.answer()
        return

    await show_error(call, state)

    
@router.message(st.admin.admin_add)
async def add_admin(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        await navigate_back_or_main(message, state, st.admin.admins, "admins_msg", await kb_i.admins(lang))
        return
    
    elif text == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    phone = text.replace(" ", "").replace("-", "")
    if not re.fullmatch(r"(\+?998\d{9})", phone):
        await show_error(message, state, "invalid_phone_number_msg")
        return
    
    await db.create_admin_by_phone(phone)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "admin_add_success_msg").format(phone=phone),
        parse_mode="HTML",
        reply_markup=await kb_i.admins(lang)
    )
    await state.set_state(st.admin.admins)    

@router.callback_query(F.data.startswith("adm_detail_btn:"), st.admin.admin_detail)
async def admin_detail(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    admin_name = data.get("admin_name")
    admin_telegram_id = data.get("admin_tg_id")

    back = "adm_detail_btn:back"
    main = "adm_detail_btn:main"
    delete = "adm_detail_btn:delete"
    phone = "adm_detail_btn:phone"
    button = "adm_detail_btn:button"

    async def go_back():
        await navigate_back_or_main(call, state, st.admin.admins, "admins_msg", await kb_i.admins(lang))

    async def go_main():
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))

    async def delete_admin():
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "admin_delete_msg").format(name=admin_name),
            parse_mode="HTML",
            reply_markup=kb_i.confirm_reject(lang)
        )
        await state.set_state(st.admin.admin_delete)

    async def edit_phone():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "admin_edit_phone_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.admin_edit_phone)

    async def edit_button():
        buttons = cf.get_admin_buttons(admin_telegram_id) or []
        await state.update_data(admin_buttons=buttons)
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "admin_edit_button_msg"),
            parse_mode="HTML",
            reply_markup=kb_i.build_admin_buttons_editor(lang, buttons)
        )
        await state.set_state(st.admin.admin_edit_button)

    handlers = {
        back: go_back,
        main: go_main,
        delete: delete_admin,
        phone: edit_phone,
        button: edit_button
    }
    handle = handlers.get(action)
    
    if handle:
        await handle()
        await call.answer()
        return
    
    await show_error(call, state)


@router.message(st.admin.admin_edit_phone)
async def edit_admin_phone(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    admin_id = data.get("admin_id")
    admin_telegram_id = data.get("admin_tg_id")
    admin_name = data.get("admin_name")
    admin_phone = data.get("admin_phone")
    admin_buttons = data.get("admin_buttons")

    button_ids = admin_buttons or cf.get_admin_buttons(admin_telegram_id)
    but_names = [cf.button_title(lang, role, bid) for bid in button_ids]
    buttons_str = ", ".join(but_names) if but_names else "—"

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
            name=admin_name or "",
            phone=admin_phone or "",
            buttons=buttons_str
        )
        await navigate_back_or_main(message, state, st.admin.admin_detail, msg, kb_i.admin_detail(lang))
        return
    
    elif text == text_main:
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return
    
    phone = text.replace(" ", "").replace("-", "")
    if not re.fullmatch(r"(\+?998\d{9})", phone):
        await show_error(message, state, "invalid_phone_number_msg")
        return

    datas = {"phone_number": phone}
    await db.update_admin_by_id(admin_id, datas)

    msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
        name=admin_name or "",
        phone=phone,
        buttons=buttons_str
    )
    await message.bot.send_message(
        user_id,
        cf.get_text(lang, role, "message", "admin_edit_phone_success_msg"),
        parse_mode="HTML",
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await state.update_data(admin_phone=phone)

    await message.bot.send_message(
        user_id,
        msg,
        parse_mode="HTML",
        reply_markup=kb_i.admin_detail(lang)
    )
    await state.set_state(st.admin.admin_detail)


@router.callback_query(F.data.startswith("adm_btn:"), st.admin.admin_edit_button)
async def admin_buttons_callbacks(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    admin_telegram_id = data.get("admin_tg_id")
    admin_name = data.get("admin_name")
    admin_phone = data.get("admin_phone")
    buttons = data.get("admin_buttons", [])

    if action == "adm_btn:back":
        button_ids = cf.get_admin_buttons(admin_telegram_id)
        but_names = [cf.button_title(lang, role, bid) for bid in button_ids]
        buttons_str = ", ".join(but_names) if but_names else "—"
        msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
            name=admin_name or "",
            phone=admin_phone or "",
            buttons=buttons_str
        )
        await navigate_back_or_main(call, state, st.admin.admin_detail, msg, kb_i.admin_detail(lang))
        return

    if action == "adm_btn:save":
        cf.set_admin_buttons(admin_telegram_id, sorted(buttons))

        but_names = [cf.button_title(lang, role, bid) for bid in buttons]
        buttons_str = ", ".join(but_names) if but_names else "—"

        msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
            name=admin_name or "",
            phone=admin_phone or "",
            buttons=buttons_str
        )

        await call.answer(cf.get_text(lang, role, "message", "admin_edit_button_success_msg"), show_alert=True)
        await call.message.edit_text(msg, parse_mode="HTML", reply_markup=kb_i.admin_detail(lang))
        await state.set_state(st.admin.admin_detail)
        await call.answer()
        return

    if action.startswith("adm_btn:toggle:"):
        try:
            _, _, bid = action.split(":", 2)
        except ValueError:
            await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)
            return

        if bid in buttons:
            buttons.remove(bid)
        else:
            buttons.append(bid)  

        new_kb = kb_i.build_admin_buttons_editor(lang, buttons)
        await state.update_data(admin_buttons=buttons)

        if call.message.reply_markup != new_kb:
            await call.message.edit_reply_markup(reply_markup=new_kb)

        await call.answer()


@router.callback_query(st.admin.admin_delete)
async def delete_admin(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)
    
    admin_telegram_id = data.get("admin_tg_id")
    admin_name = data.get("admin_name")
    admin_phone = data.get("admin_phone")

    buttons = data.get("admin_buttons", [])

    if action == "back":
        but_names = [cf.button_title(lang, role, bid) for bid in buttons]
        buttons_str = ", ".join(but_names) if but_names else "—"

        msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
            name=admin_name or "",
            phone=admin_phone or "",
            buttons=buttons_str
        )
        await navigate_back_or_main(call, state, st.admin.admin_detail, msg, kb_i.admin_detail(lang))
        return
    
    if action == "main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if action == "confirm":
        await db.delete_admin_by_phone(admin_phone)
        await cf.delete_admin_from_json(admin_telegram_id)
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "admin_deleted_msg"),
            parse_mode="HTML",
            reply_markup=None
        )
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "admins_msg"),
            parse_mode="HTML",
            reply_markup=await kb_i.admins(lang)
        )
        await state.set_state(st.admin.admins)
        return

    await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)    

########################################################## LANGUAGE ##########################################################

########################################################## INFOS && LANGUAGE ##########################################################

@router.callback_query(F.data.startswith("info_btn:"), st.admin.infos)
async def info(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    if action == "info_btn:back":
        await navigate_back_or_main(call, state, st.admin.settings, "settings_msg", kb_i.settings(lang, "admin"))
        return

    if action == "info_btn:back_main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if action == "info_btn:contact":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "info_contact_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.info_contact)
        return

    if action == "info_btn:location":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "info_location_msg"),
            reply_markup=kb_r.location_back(lang)
        )
        await state.set_state(st.admin.info_location)
        return

    if action == "info_btn:price_list":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "info_price_list_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.info_price_list)
        return

    await show_error(call, state)


@router.message(st.admin.info_contact)
async def info_contact_handler(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    if text == cf.get_text(lang, role, "button", "back"):
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await navigate_back_or_main(message, state, st.admin.infos, "infos_msg", kb_i.infos(lang))
        return

    if text == cf.get_text(lang, role, "button", "back_main"):
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return
    
    else:
        infos = text.split("\n")
        phone_number = infos[0].strip() if len(infos) > 0 else ""
        barber_shop = infos[1].strip() if len(infos) > 1 else ""

        payload = { "project_contact": { "contact": phone_number, "barber_shop": barber_shop } }

        cf.update_infos(payload)
        await message.bot.send_message(user_id, cf.get_text(lang, role, "message", "infos_updated_msg"), reply_markup=kb_r.ReplyKeyboardRemove())
        await message.answer(cf.get_text(lang, role, "message", "infos_msg"), reply_markup=kb_i.infos(lang))
        await state.set_state(st.admin.infos)
        return


@router.message(st.admin.info_location)
async def info_location_handler(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    if text == cf.get_text(lang, role, "button", "back"):
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await navigate_back_or_main(message, state, st.admin.infos, "infos_msg", kb_i.infos(lang))
        return

    if text == cf.get_text(lang, role, "button", "back_main"):
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return
    
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        await state.update_data(location={"latitude": lat, "longitude": lon})
        if not data.get("address"):
            await message.answer(cf.get_text(lang, role, "message", "ask_address_msg"))
            return

    if text and not message.location:
        address = text.strip()
        await state.update_data(address=address)
        if not data.get("location"):
            await message.answer(cf.get_text(lang, role, "message", "ask_location_msg"))
            return

    data = await state.get_data()
    location = data.get("location", {})
    address = data.get("address", "")

    if not location:
        await message.answer(cf.get_text(lang, role, "message", "location_not_set_msg"))
        return

    if not address:
        await message.answer(cf.get_text(lang, role, "message", "address_not_set_msg"))
        return

    lat = location.get("latitude")
    lon = location.get("longitude")

    payload = { "project_location": { "latitude": lat, "longitude": lon, "address": address } }

    cf.update_infos(payload)
    await message.bot.send_message(user_id, cf.get_text(lang, role, "message", "infos_updated_msg"), reply_markup=kb_r.ReplyKeyboardRemove())
    await message.answer(cf.get_text(lang, role, "message", "infos_msg"), reply_markup=kb_i.infos(lang))
    await state.update_data(location=None, address=None)
    await state.set_state(st.admin.infos)
    return


@router.message(st.admin.info_price_list)
async def info_price_list_handler(message: Message, state: FSMContext):
    user_id, data, lang, _ = await get_user_context(message, state)

    if message.text == cf.get_text(lang, role, "button", "back"):
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await navigate_back_or_main(message, state, st.admin.infos, "infos_msg", kb_i.infos(lang))
        return

    if message.text == cf.get_text(lang, role, "button", "back_main"):
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return
    
    multiline = message.text.replace("\r\n", "\n").replace("\r", "\n")
    payload = { "project_price_list": { "message": multiline } }
    cf.update_infos(payload)

    await message.bot.send_message(user_id, cf.get_text(lang, role, "message", "infos_updated_msg"), reply_markup=kb_r.ReplyKeyboardRemove())
    await message.answer(cf.get_text(lang, role, "message", "infos_msg"), reply_markup=kb_i.infos(lang))
    await state.set_state(st.admin.infos)
    return


@router.callback_query(F.data.startswith("language_btn:"), st.admin.language)
async def language(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)
    
    text_uz = "language_btn:uz"
    text_ru = "language_btn:ru"
    
    if action == "language_btn:back":
        await navigate_back_or_main(call, state, st.admin.settings, "settings_msg", kb_i.settings(lang, "admin"))
        return
    
    if action == "language_btn:main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    if action == text_uz or action == text_ru:
        lang_code = "🇺🇿 uz" if action == text_uz else "🇷🇺 ru"
        await state.update_data(lang=lang_code)  
        admin = await db.get_user_by_id(telegram_id=user_id)
        admin_id = admin.get("id")
        datas = {"language": action.split(":")[1]}
        await db.update_admin_by_id(admin_id, datas)

        await call.message.edit_text(
            cf.get_text(lang_code, role, "message", "language_selected_msg"),
            reply_markup=None
        )
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "settings_msg"),
            parse_mode="HTML",
            reply_markup=kb_i.settings(lang=lang_code, manager="admin")
        )
        await state.set_state(st.admin.settings)
        return
    
    await show_error(call, state)

#################################################### SETTINGS MENU ##############################################################

#################################################### CLIENTS MENU ##############################################################

@router.callback_query(F.data.startswith("client_btn:"), st.admin.clients)
async def clients(call: CallbackQuery, state: FSMContext):
    user_id, data, lang, action = await get_user_context(call, state)

    if action == "client_btn:main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return
    
    if action == "client_btn:search":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "client_search_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.admin.client_search)
        return
    
    if action == "client_btn:list":
        all_clients = await db.get_clients_all()

        if not all_clients:
            await call.answer(cf.get_text(lang, role, "message", "clients_not_msg"), show_alert=True)
            return

        last_clients = all_clients[-5:]
        await call.message.delete()
        await call.bot.send_document(
            user_id,
            document=cf.generate_clients_csv(all_clients),
            caption=cf.get_text(lang, role, "message", "client_list_msg")
        )
        await call.bot.send_message(
            user_id,
            get_clients_info(lang, last_clients),
            parse_mode="HTML",
            reply_markup=kb_i.back_main(lang)
        )
        await state.set_state(st.admin.client_list)
        return

    await show_error(call, state)


@router.callback_query(st.admin.client_list)
async def client_list(call: CallbackQuery, state: FSMContext):
    user_id, _, lang, action = await get_user_context(call, state)

    if action == "back":
        await navigate_back_or_main(call, state, st.admin.clients, "clients_msg", kb_i.clients(lang))
        return
    
    if action == "main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return
    
    await show_error(call, state)


@router.message(st.admin.client_search)
async def client_search(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    t_back = cf.get_text(lang, role, "button", "back")
    t_main = cf.get_text(lang, role, "button", "back_main")

    if text == t_back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await navigate_back_or_main(message, state, st.admin.clients, "clients_msg", kb_i.clients(lang))
        return
    
    if text == t_main: 
        await navigate_back_or_main(message, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    phone = text.replace(" ", "").replace("-", "")
    if not re.fullmatch(r"(\+?998\d{9})", phone):
        await show_error(message, state, "invalid_phone_number_msg")
        return
    
    client = await db.get_client_by_phone(phone)

    if not client:
        await message.bot.send_message(user_id, cf.get_text(lang, role, "message", "client_not_found_msg"), parse_mode="HTML")
        return
    
    user_ban = 5 in (client.get("roles") or [])

    await state.update_data(client_tg_id=client.get("telegram_id"))
    await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
    await message.bot.send_message(
        user_id,
        get_client_card(lang, client),
        parse_mode="HTML",
        reply_markup=kb_i.client_detail(lang, client.get("telegram_id"), user_ban)
    )
    await state.set_state(st.admin.client_detail)


@router.callback_query(F.data.startswith("cnt_detail_btn:"), st.admin.client_detail)
async def client_detail(call: CallbackQuery, state: FSMContext):
    from handlers.register_handlers import ban_mw
    user_id, data, lang, action = await get_user_context(call, state)

    if action == "cnt_detail_btn:back":
        await navigate_back_or_main(call, state, st.admin.clients, "clients_msg", kb_i.clients(lang))
        return

    if action == "cnt_detail_btn:main":
        await navigate_back_or_main(call, state, st.admin.main_menu, "main_menu_msg", kb_r.ad_main_menu(lang, user_id))
        return

    client_telegram_id = data.get("client_tg_id")
    client = await db.get_user_by_id(telegram_id=client_telegram_id)

    if action in ("cnt_detail_btn:ban", "cnt_detail_btn:unban"):
        action = action.split(":")[1]
        if action == "ban":
            await db.ban_client_by_phone(client.get("phone_number"))
            msg_key = "client_ban_msg"
        else:
            await db.unban_client_by_phone(client.get("phone_number"))
            msg_key = "client_unban_msg"

        ban_mw.invalidate(client_telegram_id)
        client = await db.get_user_by_id(telegram_id=client_telegram_id)
        user_ban = 5 in (client.get("roles") or [])

        await call.answer(cf.get_text(lang, role, "message", msg_key), show_alert=True)
        await call.message.edit_text(
            get_client_card(lang, client),
            parse_mode="HTML",
            reply_markup=kb_i.client_detail(lang, client_telegram_id, user_ban)
        )
        return

    await show_error(call, state)

##################################################################################################################

@router.message(st.admin.analytics)
async def analytics(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text


##################################################################################################################