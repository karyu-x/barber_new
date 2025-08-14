import asyncio
import re
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from configs import functions as cf
from configs import buttons_config as butt_cf
from databases.director import database as db
from states.director import state as st
from keyboards.director import reply as kb_r
from keyboards.director import inline as kb_i

director_router = Router()
router = director_router

log = logging.getLogger(__name__)

role = "director"

DURATION_RE = re.compile(r"^\d{1,3}$")
PRICE_RE = re.compile(r"\d+")

def _parse_price(s: str) -> int | None:
    digits = "".join(PRICE_RE.findall(s))
    if not digits:
        return None
    return int(digits)

# === Utils ===
async def get_user_context(message, state):
    "Возвращает (user_id, data, lang, text)"
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = getattr(message, "text", None)
    return user_id, data, lang, text


async def handle_back_navigation(message, state, target_state, target_text, target_markup):
    user_id, _, lang, _ = await get_user_context(message, state)

    # Получаем текст
    if isinstance(target_text, str) and not target_text.startswith("<") and " " not in target_text:
        # Похоже на ключ (без пробелов, тэгов и т.д.)
        final_text = cf.get_text(lang, role, "message", target_text)
    else:
        final_text = target_text

    # Получаем клавиатуру
    if callable(target_markup):
        reply_markup = target_markup(lang)
    else:
        reply_markup = target_markup

    await message.bot.send_message(user_id, final_text, parse_mode="HTML", reply_markup=reply_markup)
    await state.set_state(target_state)


async def send_error(message, state, error_key: str = "unknown_command"):
    user_id, _, lang, _ = await get_user_context(message, state)
    await message.bot.send_message(chat_id=user_id, text=cf.get_text(lang, "errors", error_key))


async def _get_services_text(lang, role, type_id, type_name):
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



async def _service_detail_text(lang, role, item: dict) -> str:
    body = cf.get_text(lang, role, "message", "service_detail_msg").format(
        description=item.get("description") or "-",
        duration=item.get("duration") or "-",
        price=f"{(item.get('price') or 0):,}"
    )
    return f"<b>{item['name']}</b>\n\n{body}"

async def _send_barber_card(message, lang, barber, state):
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
    await message.bot.send_message(
        chat_id=message.from_user.id,
        text=text_reply,
        parse_mode="HTML",
        reply_markup=kb_i.barber_detail(lang)
    )
    await state.set_state(st.director.barber_detail)

##################################################################################################################

@router.message(st.director.main_menu)
async def main_menu(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    buttons = await butt_cf.get_main_buttons(lang)
    
    if text == cf.get_text(lang, role, "button", "settings"):
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "settings_msg"),
            parse_mode="HTML",
            reply_markup=kb_i.settings(lang)
        )
        await state.set_state(st.director.settings)
        return

    for key, config in buttons.items():
        if text == cf.get_text(lang, role, "button", key):
            reply_text = cf.get_text(lang, role, "message", config["message"])
            reply_markup = config["keyboard"]
            await message.bot.send_message(
                chat_id=user_id,
                text=reply_text, 
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            await state.set_state(config["state"])
            return
    
    await send_error(message, state)

##################################################################################################################

@router.message(st.director.notifications)
async def notifications(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    for key, config in butt_cf.NOTIFICATIONS_BUTTONS.items():
        if text == cf.get_text(lang, role, "button", key):
            reply_text = cf.get_text(lang, role, "message", config["message"])
            reply_makrup = config["keyboard"](lang)
            await message.bot.send_message(
                chat_id=user_id,
                text=reply_text,
                parse_mode="HTML",
                reply_markup=reply_makrup
            )
            await state.set_state(config["state"])
            return
    
    await send_error(message, state)

### INPUT TEXT
@router.message(st.director.input_text)
async def input_text(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "notifications_msg"),
            "reply_markup": kb_r.notifications(lang),
            "state": st.director.notifications
        },
        cf.get_text(lang, role, "button", "back_main"): {
            "text": cf.get_text(lang, role, "message", "main_menu_msg"),
            "reply_markup": kb_r.main_menu(lang),
            "state": st.director.main_menu
        }
    }
    action = back_actions.get(text)

    if action:
        await message.bot.send_message(
            chat_id=user_id,
            text=action["text"],
            parse_mode="HTML",
            reply_markup=action["reply_markup"]
        )
        await state.set_state(action["state"])
        return

    reply_text = cf.get_text(lang, role, "message", "text_accepted_msg").format(text)
    await state.update_data(description=text)
    await message.bot.send_message(
        chat_id=user_id,
        text=reply_text,
        parse_mode="HTML",
        reply_markup=kb_r.notifications(lang)
    )
    await state.set_state(st.director.notifications)

### INPUT PHOTO
@router.message(st.director.input_photo)
async def input_text(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "notifications_msg"),
            "reply_markup": kb_r.notifications(lang),
            "state": st.director.notifications
        },
        cf.get_text(lang, role, "button", "back_main"): {
            "text": cf.get_text(lang, role, "message", "main_menu_msg"),
            "reply_markup": kb_r.main_menu(lang),
            "state": st.director.main_menu
        }
    }
    action = back_actions.get(text)

    if action:
        await message.bot.send_message(
            chat_id=user_id,
            text=action["text"],
            parse_mode="HTML",
            reply_markup=action["reply_markup"]
        )
        await state.set_state(action["state"])
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
        await state.set_state(st.director.notifications)
        return

    await send_error(message, state, "photo_required_msg")

### INPUT BUTTON
@router.message(st.director.input_button)
async def input_button(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "notifications_msg"),
            "reply_markup": kb_r.notifications(lang),
            "state": st.director.notifications
        },
        cf.get_text(lang, role, "button", "back_main"): {
            "text": cf.get_text(lang, role, "message", "main_menu_msg"),
            "reply_markup": kb_r.main_menu(lang),
            "state": st.director.main_menu
        }
    }
    action = back_actions.get(text)

    if action:
        await message.bot.send_message(
            chat_id=user_id,
            text=action["text"],
            parse_mode="HTML",
            reply_markup=action["reply_markup"]
        )
        await state.set_state(action["state"])
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
        await send_error(message, state, "invalid_button_format")
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
    await state.set_state(st.director.notifications)

### CHECK POST
@router.message(st.director.check_post)
async def check_post(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    text_back = cf.get_text(lang, role, "button", "back")
    text_back_main = cf.get_text(lang, role, "button", "back_main")
    text_preview = cf.get_text(lang, role, "button", "preview_post")
    text_confirm = cf.get_text(lang, role, "button", "confirm_post")

    async def handle_back():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "notifications_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.notifications(lang)
        )
        await state.set_state(st.director.notifications)

    async def handle_back_main():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)

    async def handle_preview():
        text = data.get("description", "NO MESSAGE")
        photo = data.get("photo", "")
        buttons = data.get("buttons", [])
        markup = kb_i.post_button(buttons) if buttons else None

        if photo:
            await message.bot.send_photo(
                chat_id=user_id,
                photo=photo,
                caption=text,
                reply_markup=markup
            )
        else:
            await message.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=markup
            )

    async def handle_send():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "confirm_post_msg"),
            reply_markup=kb_r.confirm_reject(lang)
        )
        await state.set_state(st.director.confirm_post)

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
    
    await send_error(message, state)

### CONFIRM POST
@router.message(st.director.confirm_post)
async def confirm_post(message: Message, state: FSMContext):
    user_id, data, lang, _ = await get_user_context(message, state)
    text = (message.text or "").strip()
    if text != cf.get_text(lang, role, "button", "send"):
        await send_error(message, state, "unknown_command")
        return

    description = data.get("description")
    photo = data.get("photo")
    buttons = data.get("buttons", [])
    reply_markup = kb_i.post_button(buttons) if buttons else None

    users = await db.get_users_all()
    sem = asyncio.Semaphore(20)
    success = 0
    failed = 0

    async def send_one(uid: int):
        nonlocal success, failed
        async with sem:
            try:
                if photo:
                    await message.bot.send_photo(uid, photo, caption=description, reply_markup=reply_markup, parse_mode="HTML")
                else:
                    await message.bot.send_message(uid, description, reply_markup=reply_markup, parse_mode="HTML")
                success += 1
            except Exception as e:
                failed += 1
                log.warning("Broadcast fail uid=%s: %s", uid, e)

    CHUNK = 200
    for i in range(0, len(users), CHUNK):
        chunk = users[i:i+CHUNK]
        await asyncio.gather(*(send_one(u["telegram_id"]) for u in chunk))

    await state.update_data(description=None, photo=None, buttons=None)
    await message.bot.send_message(user_id, f"📤 Отправлено: {success}\n❌ Ошибок: {failed}")
    await message.bot.send_message(user_id, cf.get_text(lang, role, "message", "main_menu_msg"), parse_mode="HTML", reply_markup=kb_r.main_menu(lang))
    await state.set_state(st.director.main_menu)

@router.message(st.director.bookings)
async def bookings(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    for key, config in butt_cf.BOOKINGS_BUTTONS.items():
        if text == cf.get_text(lang, role, "button", key):
            reply_text = cf.get_text(lang, role, "message", config["message"])
            reply_markup = config["keyboard"](lang)
            await message.bot.send_message(
                chat_id=user_id,
                text=reply_text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            await state.set_state(config["state"])
            return
        
    await send_error(message, state)

### TODAY BOOKS
@router.message(st.director.today_books)
async def today_books(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    if text == cf.get_text(lang, role, "button", "back"):
        await handle_back_navigation(message, state, st.director.bookings, "bookings_msg", kb_r.bookings)
        return
    
    elif text == cf.get_text(lang, role, "button", "back_main"):
        await handle_back_navigation(message, state, st.director.main_menu, "main_menu_msg", kb_r.main_menu)
        return

    barbers = await db.get_barbers_all()
    for item in barbers:
        if text == item["first_name"]:
            await state.update_data(barber_tg_id=item["telegram_id"],
                                    barber_name=text)
            await message.bot.send_message(
                chat_id=user_id,
                text=cf.get_text(lang, role, "message", "barber_books_msg"),
                reply_markup=await kb_r.barber_books(item["telegram_id"])
            )
            await state.set_state(st.director.barber_books)
            return
    
    await send_error(message, state)


### OTHER DAY BOOKS
@router.message(st.director.other_day_books)
async def other_day_books(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    await send_error(message, state)

### CANCEL BOOKS
@router.message(st.director.cancel_books)
async def cancel_books(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    await send_error(message, state)

### RESCHEDULE BOOKS
@router.message(st.director.reschedule_books)
async def reschedule_books(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)

    await send_error(message, state)
    
#################################################### SETTINGS MENU ##############################################################

@router.callback_query(F.data.startswith("setting_btn:"), st.director.settings)
async def settings(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    buttons = await butt_cf.get_setting_buttons(lang)
    action = call.data

    if action == "setting_btn:back":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        await call.answer()
        return

    for key, config in buttons.items():
        if action == f"setting_btn:{key}":
            reply_text = cf.get_text(lang, role, "message", config["message"])
            reply_markup = config["keyboard"]
            await call.message.edit_text(
                text=reply_text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            await state.set_state(config["state"])
            await call.answer()
            return
        
    await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)

########################################################## SERVICE & PRICE ##########################################################

@router.callback_query(F.data.startswith("services_btn:"), st.director.services_prices)
async def services_prices(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")

    action = call.data

    if action == "services_btn:back":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "settings_msg"),
            parse_mode="HTML",
            reply_markup=kb_i.settings(lang)
        )
        await state.set_state(st.director.settings)
        await call.answer()
        return
    
    if action == "services_btn:main":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        await call.answer()
        return

    parts = action.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        barber_telegram_id = int(parts[1])
        barber = await db.get_barber_by_id(barber_telegram_id)
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

        await state.set_state(st.director.barber_types)
        await call.answer()
        return




@router.callback_query(F.data.startswith("types_btn:"), st.director.barber_types)
async def barber_types(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    barber_telegram_id = data.get("barber_tg_id")

    action = call.data

    if action == "types_btn:back":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "services_prices_msg"),
            parse_mode="HTML",
            reply_markup=await kb_i.services_prices(lang)
        )
        await state.set_state(st.director.services_prices)
        await call.answer()
        return
    
    if action == "types_btn:main":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        await call.answer()
        return

    if action == "types_btn:add":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "type_add_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.add_type)
        await call.answer()
        return

    parts = action.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        type_id = int(parts[1])
        service_type = await db.get_barber_type_by_id(barber_telegram_id, type_id)
        if not service_type:
            await call.answer(cf.get_text(lang, role, "message", "type_not_found_msg"), show_alert=True)
            return

        await state.update_data(
            service_type_id=type_id,
            service_type_name=service_type["name"]
        )

        services_text = await _get_services_text(lang, role, type_id, service_type["name"])

        await call.message.edit_text(
            services_text,
            parse_mode="HTML",
            reply_markup=await kb_i.barber_services(lang, type_id)
        )
        await state.set_state(st.director.barber_services)
        await call.answer()
        return


@router.message(st.director.add_type)
async def add_type(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    barber_id, barber_telegram_id, barber_name = data.get("barber_id"), data.get("barber_tg_id"), data.get("barber_name")

    text = message.text
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
        await state.set_state(st.director.barber_types)
        return
    
    if text == main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
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
    await state.set_state(st.director.barber_types)


@router.callback_query(st.director.delete_type)
async def delete_type(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")

    barber_telegram_id = data.get("barber_tg_id")
    barber_name = data.get("barber_name") 
    type_name = data.get("service_type_name")
    type_id = data.get("service_type_id")

    action = call.data

    if action == "back":
        services_text = await _get_services_text(lang, role, type_id, type_name)
        await call.message.edit_text(
            services_text,
            parse_mode="HTML",
            reply_markup=await kb_i.barber_services(lang, type_id)
        )
        await state.set_state(st.director.barber_services)
        await call.answer()
        return

    if action == "main":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
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
        await state.set_state(st.director.barber_types)
        await call.answer()
        return

    await call.answer(cf.get_text(lang, "errors", "unknown_command"))    


@router.callback_query(F.data.startswith("service_btn:"), st.director.barber_services)
async def barber_services(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")

    barber_telegram_id = data.get("barber_tg_id")
    barber_name = data.get("barber_name")
    type_id = data.get("service_type_id")

    action = call.data

    if action == "service_btn:back":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "service_types_msg").format(barber=barber_name or ""),
            parse_mode="HTML",
            reply_markup=await kb_i.barber_types(lang, barber_telegram_id)
        )
        await state.set_state(st.director.barber_types)
        await call.answer()
        return

    if action == "service_btn:main":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        await call.answer()
        return

    if action == "service_btn:delete":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "type_delete_msg"),
            parse_mode="HTML",
            reply_markup=kb_i.confirm_reject(lang)
        )
        await state.set_state(st.director.delete_type)
        await call.answer()
        return

    if action == "service_btn:add":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "service_add_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.add_service)
        await call.answer()
        return

    parts = action.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        service_id = int(parts[1])

        item = await db.get_barber_service_by_id(type_id, service_id)
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
        await state.set_state(st.director.service_detail)
        await call.answer()
        return

    await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)


@router.message(st.director.add_service)
async def add_service(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    type_id = data.get("service_type_id")
    type_name =  data.get("service_type_name")
    text = message.text

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return

    if text == text_back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        services_text = await _get_services_text(lang, role, type_id, type_name)
        await message.bot.send_message(
            user_id,
            services_text,
            parse_mode="HTML",
            reply_markup=await kb_i.barber_services(lang, type_id)
        )
        await state.set_state(st.director.barber_services)
        return

    datas = {"name": text, "service_type": type_id}
    await db.create_barber_service(datas)

    services_text = await _get_services_text(lang, role, type_id, type_name)
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
    await state.set_state(st.director.barber_services)


@router.callback_query(st.director.delete_service)
async def delete_service(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")

    type_id = data.get("service_type_id")
    service_id = data.get("service_id")
    type_name = data.get("service_type_name")
    
    action = call.data

    if action == "confirm":
        await db.delete_barber_service_by_id(service_id)
        services_text = await _get_services_text(lang, role, type_id, type_name)

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
        await state.set_state(st.director.barber_services)
        await call.answer()
        return

    if action == "back":
        item = await db.get_barber_service_by_id(type_id, service_id)
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
        await state.set_state(st.director.barber_services)
        await call.answer()
        return

    if action == "main":
        await call.message.delete()
        await call.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang),
        )
        await call.answer()
        await state.set_state(st.director.main_menu)
        return
    
    await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)


@router.callback_query(F.data.startswith("ser_detail_btn:"), st.director.service_detail)
async def service_detail(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")

    type_id = data.get("service_type_id")
    type_name = data.get("service_type_name")
    service_id = data.get("service_id")
    action = call.data

    async def handle_name():
        await call.message.delete()
        await call.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_edit_name_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_service_name)

    async def handle_description():
        await call.message.delete()
        await call.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_edit_description_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_service_description)

    async def handle_duration():
        await call.message.delete()
        await call.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_edit_duration_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_service_duration)

    async def handle_price():
        await call.message.delete()
        await call.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_edit_price_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_service_price)

    async def handle_back():
        services_text = await _get_services_text(lang, role, type_id, type_name)
        await call.message.edit_text(
            services_text,
            parse_mode="HTML",
            reply_markup=await kb_i.barber_services(lang, type_id)
        )
        await state.set_state(st.director.barber_services)

    async def handle_main():
        await call.message.delete()
        await call.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)

    async def handle_delete():
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "service_delete_msg"),
            reply_markup=kb_i.confirm_reject(lang)
        )
        await state.set_state(st.director.delete_service)

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


@router.message(st.director.edit_service_name)
async def edit_service_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    
    type_id = data.get("service_type_id")
    service_id = data.get("service_id")

    text = message.text
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        item = await db.get_barber_service_by_id(type_id, service_id)
        service_info = await _service_detail_text(lang, role, item)
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await message.bot.send_message(
            user_id,
            service_info,
            parse_mode="HTML",
            reply_markup=kb_i.service_detail(lang)
        )
        await state.set_state(st.director.service_detail)
        return

    if text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return

    datas = {"id": service_id, "name": text.strip()}
    await db.update_barber_service_by_id(service_id, datas)

    item = await db.get_barber_service_by_id(type_id, service_id)
    service_info = await _service_detail_text(lang, role, item)
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
    await state.set_state(st.director.service_detail)


@router.message(st.director.edit_service_description)
async def edit_service_description(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    
    type_id = data.get("service_type_id")
    service_id = data.get("service_id")

    text = message.text
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        item = await db.get_barber_service_by_id(type_id, service_id)
        service_info = await _service_detail_text(lang, role, item)
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await message.bot.send_message(
            user_id,
            service_info,
            parse_mode="HTML",
            reply_markup=kb_i.service_detail(lang)
        )
        await state.set_state(st.director.service_detail)
        return

    if text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return
    
    datas = {"id": service_id, "description": text.strip()}
    await db.update_barber_service_by_id(service_id, datas)

    item = await db.get_barber_service_by_id(type_id, service_id)
    service_info = await _service_detail_text(lang, role, item)
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
    await state.set_state(st.director.service_detail)


@router.message(st.director.edit_service_duration)
async def edit_service_duration(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    
    type_id = data.get("service_type_id")
    service_id = data.get("service_id")

    text = message.text
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        item = await db.get_barber_service_by_id(type_id, service_id)
        service_info = await _service_detail_text(lang, role, item)
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await message.bot.send_message(
            user_id,
            service_info,
            parse_mode="HTML",
            reply_markup=kb_i.service_detail(lang)
        )
        await state.set_state(st.director.service_detail)
        return

    if text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return
    
    if not DURATION_RE.match(text):
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, "errors", "invalid_duration_msg"),
            parse_mode="HTML"
        )
        return

    minutes = int(text)
    if minutes <= 0:
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, "errors", "invalid_duration_msg"),
            parse_mode="HTML"
        )
        return

    datas = {"id": service_id, "duration": minutes}
    await db.update_barber_service_by_id(service_id, datas)

    item = await db.get_barber_service_by_id(type_id, service_id)
    service_info = await _service_detail_text(lang, role, item)
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
    await state.set_state(st.director.service_detail)


@router.message(st.director.edit_service_price)
async def edit_service_price(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    
    type_id = data.get("service_type_id")
    service_id = data.get("service_id")

    text = message.text
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        item = await db.get_barber_service_by_id(type_id, service_id)
        service_info = await _service_detail_text(lang, role, item)
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        await message.bot.send_message(
            user_id,
            service_info,
            parse_mode="HTML",
            reply_markup=kb_i.service_detail(lang)
        )
        await state.set_state(st.director.service_detail)
        return

    if text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return
    
    price = _parse_price(text)
    if not price or price <= 0:
        await message.bot.send_message(
            cf.get_text(lang, "errors", "invalid_price_msg"),
            parse_mode="HTML"
        )
        return
    
    datas = {"id": service_id, "price": text}
    await db.update_barber_service_by_id(service_id, datas)
    
    item = await db.get_barber_service_by_id(type_id, service_id)
    service_info = await _service_detail_text(lang, role, item)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "service_edit_price_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await message.bot.send_message(
        user_id,
        service_info,
        parse_mode="HTML",
        reply_markup=kb_i.service_detail(lang)
    )
    await state.set_state(st.director.service_detail)

##################################################### SERVICE & PRICE #######################################################

########################################################## BARBERS ##########################################################

@router.callback_query(F.data.startswith("barber_btn:"), st.director.barbers)
async def barbers(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    action = call.data

    if action == "barber_btn:back":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "settings_msg"),
            parse_mode="HTML",
            reply_markup=kb_i.settings(lang)
        )
        await state.set_state(st.director.settings)
        await call.answer()
        return

    if action == "barber_btn:main":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        await call.answer()
        return

    if action == "barber_btn:add":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barber_add_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.add_barber)
        await call.answer()
        return

    parts = action.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        barber_id = int(parts[1])
        barber = await db.get_barber_by_id(int(barber_id))
        if not barber:
            await call.answer(cf.get_text(lang, role, "message", "barber_not_found_msg"), show_alert=True)
            return
        
        barber_data = {
            "name": barber["first_name"] or "❌",
            "phone_number": barber["phone_number"] or "❌",
            "description": barber["description"] or "❌",
            "rating": barber["rating"] or "❌",
            "from_hour": barber["default_from_hour"][:5] if barber["default_from_hour"] else "❌",
            "to_hour": barber["default_to_hour"][:5] if barber["default_to_hour"] else "❌",
            "photo": "✅" if barber["photo"] else "❌"
        }

        text_reply = cf.get_text(lang, role, "message", "barber_info_msg").format(**barber_data)
        await state.update_data(barber_tg_id=barber["telegram_id"], barber_name=barber["first_name"])
        await call.message.edit_text(
            text_reply,
            parse_mode="HTML",
            reply_markup=kb_i.barber_detail(lang)
        )

        await state.set_state(st.director.barber_detail)
        await call.answer()
        return
    
    await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)
    

@router.message(st.director.add_barber)
async def add_barber(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")

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
        await state.set_state(st.director.barbers)
        return

    if text == t_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return

    phone = text.replace(" ", "").replace("-", "")
    if not re.fullmatch(r"(\+?998\d{9})", phone):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, "errors", "invalid_phone_number_msg")
        )
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
    await state.set_state(st.director.barbers)


@router.callback_query(F.data.startswith("bar_detail_btn:"), st.director.barber_detail)
async def barber_detail(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    barber_name = data.get("barber_name")
    action = call.data

    async def go_back():
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "barbers_msg"),
            parse_mode="HTML",
            reply_markup=await kb_i.barbers(lang)
        )
        await state.set_state(st.director.barbers)

    async def go_main():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)

    async def barber_delete():
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "barber_delete_msg").format(barber_name=barber_name),
            parse_mode="HTML",
            reply_markup=kb_i.confirm_reject(lang)
        )
        await state.set_state(st.director.delete_barber)

    async def phone_edit():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barber_edit_phone_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_barber_phone)

    async def description_edit():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barber_edit_description_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_barber_description)

    async def photo_edit():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barber_edit_photo_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_barber_photo)

    async def time_edit():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "barber_edit_time_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_barber_time)

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
    
    await call.answer(cf.get_text(lang, role, "message", "invalid_command_msg"), show_alert=True)


@router.message(st.director.edit_barber_phone)
async def edit_barber_phone(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    telegram_id = data.get("barber_tg_id")

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return

    if text == text_back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        barber = await db.get_barber_by_id(telegram_id)
        await _send_barber_card(message, lang, barber, state)
        return True

    text = message.text.strip()
    if not re.match(r"^\+?998\d{9}$", text):
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, "errors", "invalid_phone_number_msg")
        )
        return

    await db.update_barber_by_id(telegram_id, data)
    barber = await db.get_barber_by_id(telegram_id)
    await message.bot.send_message(
        user_id,
        cf.get_text(lang, role, "message", "barber_edit_phone_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await _send_barber_card(message, lang, barber, state)


@router.message(st.director.edit_barber_description)
async def edit_barber_description(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    telegram_id = data.get("barber_tg_id")

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return

    if text == text_back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        barber = await db.get_barber_by_id(telegram_id)
        await _send_barber_card(message, lang, barber, state)
        return

    # await db.update_barber_by_id(telegram_id, data)
    barber = await db.get_barber_by_id(telegram_id)
    await message.bot.send_message(
        user_id,
        cf.get_text(lang, role, "message", "barber_edit_description_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await _send_barber_card(message, lang, barber, state)


@router.message(st.director.edit_barber_photo)
async def edit_barber_photo(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    telegram_id = data.get("barber_tg_id")

    text_main = cf.get_text(lang, role, "button", "back_main")
    text_back = cf.get_text(lang, role, "button", "back")

    if message.text and message.text.strip() == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return

    if message.text and message.text.strip() == text_back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        barber = await db.get_barber_by_id(telegram_id)
        await _send_barber_card(message, lang, barber, state)
        return

    if not message.photo:
        await message.bot.send_message(
            user_id,
            cf.get_text(lang, "errors", "photo_required_msg")
        )
        return

    photo_id = message.photo[-1].file_id
    # await db.update_barber_by_id(telegram_id, data)
    barber = await db.get_barber_by_id(telegram_id)
    await message.bot.send_message(
        user_id,
        cf.get_text(lang, role, "message", "barber_edit_photo_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await _send_barber_card(message, lang, barber, state)


@router.message(st.director.edit_barber_time)
async def edit_barber_time(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    telegram_id = data.get("barber_tg_id")

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return

    if text == text_back:
        await cf.get_random_modes(message, user_id, kb_r.ReplyKeyboardRemove)
        barber = await db.get_barber_by_id(telegram_id)
        await _send_barber_card(message, lang, barber, state)
        return

    if not re.match(r"^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}$", text):
        await message.bot.send_message(
            chat_id=user_id, 
            text=cf.get_text(lang, "errors", "invalid_time_range_msg")
        )
        return

    try:
        from_hour, to_hour = [t.strip() for t in text.split("-")]
        h1, m1 = map(int, from_hour.split(":"))
        h2, m2 = map(int, to_hour.split(":"))
        if not (0 <= h1 < 24 and 0 <= h2 < 24 and 0 <= m1 < 60 and 0 <= m2 < 60):
            raise ValueError
    except ValueError:
        await message.bot.send_message(
            chat_id=user_id, 
            text=cf.get_text(lang, "errors", "invalid_time_range_msg")
        )
        return

    # await db.update_barber_by_id(telegram_id, data)
    barber = await db.get_barber_by_id(telegram_id)
    await message.bot.send_message(
        user_id,
        cf.get_text(lang, role, "message", "barber_edit_time_success_msg"),
        reply_markup=kb_r.ReplyKeyboardRemove()
    )
    await _send_barber_card(message, lang, barber, state)


@router.callback_query(st.director.delete_barber)
async def delete_barber(call: CallbackQuery, state:FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    telegram_id = data.get("barber_tg_id")
    barber = await db.get_barber_by_id(telegram_id)

    action = call.data

    if action == "back":
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
        await call.message.edit_text(
            text_reply,
            parse_mode="HTML",
            reply_markup=kb_i.barber_detail(lang)
        )
        await state.set_state(st.director.barber_detail)
        await call.answer()
        return

    if action == "main":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        await call.answer()
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
        await state.set_state(st.director.barbers)
        await call.answer()
        return

########################################################## WORKING HOURS ##########################################################

@router.message(st.director.working_hours)
async def working_hours(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "settings_msg"),
            "reply_markup": kb_r.settings(lang),
            "state": st.director.settings
        },
        cf.get_text(lang, role, "button", "back_main"): {
            "text": cf.get_text(lang, role, "message", "main_menu_msg"),
            "reply_markup": kb_r.main_menu(lang),
            "state": st.director.main_menu
        }
    }
    action = back_actions.get(message.text)
    
    if action:
        await message.bot.send_message(
            chat_id=user_id,
            text=action["text"],
            parse_mode="HTML",
            reply_markup=action["reply_markup"]
        )
        await state.set_state(action["state"])
        return

########################################################## ADMINS ##########################################################

@router.callback_query(F.data.startswith("admin_btn:"), st.director.admins)
async def admins(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")

    action = call.data

    if action == "admin_btn:back":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "settings_msg"),
            parse_mode="HTML",
            reply_markup=kb_i.settings(lang)
        )
        await state.set_state(st.director.settings)
        await call.answer()
        return
    
    if action == "admin_btn:main":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        await call.answer()
        return

    if action == "admin_btn:add":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "admin_add_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.add_admin)
        await call.answer()
        return
    
    parts = action.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        admin_id = int(parts[1])
        
        admin = await db.get_admin_by_id(admin_id)
        if not admin:
            await call.answer(cf.get_text(lang, role, "message", "admin_not_found_msg"), show_alert=True)
            return

        await state.update_data(admin_id=admin.get("id"),
                                admin_tg_id=admin_id,
                                admin_name=admin.get("first_name"),
                                admin_phone=admin.get("phone_number"))

        button_ids = cf.get_admin_buttons(admin_id) or []
        but_names = [butt_cf.button_title(lang, role, bid) for bid in button_ids]
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
        
        await state.set_state(st.director.admin_detail)
        await call.answer()
        return

    await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)

    
@router.message(st.director.add_admin)
async def add_admin(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        await handle_back_navigation(message, state, st.director.admins, "admins_msg", await kb_i.admins(lang))
        return
    
    elif text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return

    phone = text.replace(" ", "").replace("-", "")
    if not re.fullmatch(r"(\+?998\d{9})", phone):
        await send_error(message, state, "invalid_phone_number_msg")
        return
    
    await db.create_admin_by_phone(phone)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "admin_add_success_msg").format(phone=phone),
        parse_mode="HTML",
        reply_markup=await kb_i.admins(lang)
    )
    await state.set_state(st.director.admins)    

@router.callback_query(F.data.startswith("adm_detail_btn:"), st.director.admin_detail)
async def admin_detail(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    admin_name = data.get("admin_name")
    admin_telegram_id = data.get("admin_tg_id")

    action = call.data
    back = "adm_detail_btn:back"
    main = "adm_detail_btn:main"
    delete = "adm_detail_btn:delete"
    phone = "adm_detail_btn:phone"
    button = "adm_detail_btn:button"

    async def go_back():
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "admins_msg"),
            parse_mode="HTML",
            reply_markup=await kb_i.admins(lang)
        )
        await state.set_state(st.director.admins)

    async def go_main():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)

    async def delete_admin():
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "admin_delete_msg").format(name=admin_name),
            parse_mode="HTML",
            reply_markup=kb_i.confirm_reject(lang)
        )
        await state.set_state(st.director.delete_admin)

    async def edit_phone():
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "admin_edit_phone_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_admin_phone)

    async def edit_button():
        buttons = cf.get_admin_buttons(admin_telegram_id) or []
        await state.update_data(admin_buttons=buttons)
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "admin_edit_button_msg"),
            parse_mode="HTML",
            reply_markup=kb_i.build_admin_buttons_editor(lang, buttons)
        )
        await state.set_state(st.director.edit_admin_button)

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
    
    await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)


@router.message(st.director.edit_admin_phone)
async def edit_admin_phone(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    admin_telegram_id = data.get("admin_telegram_id")
    admin_name = data.get("admin_name")
    admin_phone = data.get("admin_phone")

    button_ids = cf.get_admin_buttons(admin_telegram_id) or []
    but_names = [butt_cf.button_title(lang, role, bid) for bid in button_ids]
    buttons_str = ", ".join(but_names) if but_names else "—"

    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
            name=admin_name or "",
            phone=admin_phone or "",
            buttons=buttons_str
        )
        await handle_back_navigation(message, state, st.director.admin_detail, msg, kb_i.admin_detail(lang))
        return
    
    elif text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return
    
    phone = text.replace(" ", "").replace("-", "")
    if not re.fullmatch(r"(\+?998\d{9})", phone):
        await send_error(message, state, "invalid_phone_number_msg")
        return

    # await db.update_admin_by_id()
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
    await message.bot.send_message(
        user_id,
        msg,
        parse_mode="HTML",
        reply_markup=kb_i.admin_detail(lang)
    )
    await state.set_state(st.director.admin_detail)


@router.callback_query(F.data.startswith("adm_btn:"), st.director.edit_admin_button)
async def admin_buttons_callbacks(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    admin_telegram_id = data.get("admin_tg_id")
    admin_name = data.get("admin_name")
    admin_phone = data.get("admin_phone")

    buttons = data.get("admin_buttons", [])
    action = call.data

    if action == "adm_btn:back":
        button_ids = cf.get_admin_buttons(admin_telegram_id)
        but_names = [butt_cf.button_title(lang, role, bid) for bid in button_ids]
        buttons_str = ", ".join(but_names) if but_names else "—"

        msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
            name=admin_name or "",
            phone=admin_phone or "",
            buttons=buttons_str
        )
        await call.message.edit_text(msg, parse_mode="HTML", reply_markup=kb_i.admin_detail(lang))
        await state.set_state(st.director.admin_detail)
        await call.answer()
        return

    if action == "adm_btn:save":
        cf.set_admin_buttons(admin_telegram_id, sorted(buttons))

        but_names = [butt_cf.button_title(lang, role, bid) for bid in buttons]
        buttons_str = ", ".join(but_names) if but_names else "—"

        msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
            name=admin_name or "",
            phone=admin_phone or "",
            buttons=buttons_str
        )

        await call.answer(cf.get_text(lang, role, "message", "admin_edit_button_success_msg"), show_alert=True)
        await call.message.edit_text(msg, parse_mode="HTML", reply_markup=kb_i.admin_detail(lang))
        await state.set_state(st.director.admin_detail)
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

        if call.message.reply_markup != new_kb:
            await call.message.edit_reply_markup(reply_markup=new_kb)

        await call.answer()


@router.callback_query(st.director.delete_admin)
async def delete_admin(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    admin_telegram_id = data.get("admin_tg_id")
    admin_name = data.get("admin_name")
    admin_phone = data.get("admin_phone")

    buttons = data.get("admin_buttons", [])
    action = call.data

    if action == "back":
        but_names = [butt_cf.button_title(lang, role, bid) for bid in buttons]
        buttons_str = ", ".join(but_names) if but_names else "—"

        msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
            name=admin_name or "",
            phone=admin_phone or "",
            buttons=buttons_str
        )
        await call.message.edit_text(msg, parse_mode="HTML", reply_markup=kb_i.admin_detail(lang))
        await state.set_state(st.director.admin_detail)
        await call.answer()
        return
    
    if action == "main":
        await call.message.delete()
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
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
        await state.set_state(st.director.admins)
        return

    await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)    

########################################################## LANGUAGE ##########################################################

@router.callback_query(F.data.startswith("language_btn:"), st.director.language)
async def language(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    action = call.data  # Данные из callback

    text_uz = "language_btn:uz"
    text_ru = "language_btn:ru"
    

    if action == "language_btn:back":
        await call.message.edit_text(
            cf.get_text(lang, role, "message", "settings_msg"),
            parse_mode="HTML",
            reply_markup=kb_i.settings(lang)
        )
        await state.set_state(st.director.settings)
        return

    if action == "language_btn:main":
        await call.message.delete()  
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        return

    if action == text_uz or action == text_ru:
        lang_code = "🇺🇿 uz" if action == text_uz else "🇷🇺 ru"
        await state.update_data(lang=lang_code)  
        # await db.update_lang()

        await call.message.edit_text(
            cf.get_text(lang_code, role, "message", "language_selected_msg"),
            reply_markup=None
        )
        await call.bot.send_message(
            user_id,
            cf.get_text(lang, role, "message", "settings_msg"),
            parse_mode="HTML",
            reply_markup=kb_i.settings(lang=lang_code)
        )
        await state.set_state(st.director.settings)
        return

    await call.answer(cf.get_text(lang, "errors", "unknown_command"), show_alert=True)

#################################################### SETTINGS MENU ##############################################################

#################################################### CLIENTS MENU ##############################################################

@router.message(st.director.clients)
async def clients(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text

##################################################################################################################

@router.message(st.director.analytics)
async def analytics(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text

##################################################################################################################

@router.message(st.director.finance)
async def finance(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text

##################################################################################################################

@router.message(st.director.journal)
async def journal(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text

##################################################################################################################

@router.message(st.director.feedback)
async def feedback(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text

    text_back = cf.get_text(lang, role, "button", "back")
    text_rating = cf.get_text(lang, role, "button", "feedback_rating")
    text_feedback = cf.get_text(lang, role, "button", "feedback_reviews")
    text_complaint = cf.get_text(lang, role, "button", "feedback_complaints")
    text_pin = cf.get_text(lang, role, "button", "feedback_pinned")

    async def handle_back():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)

    async def handle_ratings():
        rating_barbes = db.rating_barbers()
        sorted_ratings = sorted(rating_barbes.items(), key=lambda x: x[1], reverse=True)
        reply_text = f"{cf.get_text(lang, role, 'message', 'rating_barbers_msg')}\n\n"
        for i, (name, score) in enumerate(sorted_ratings, start=1):
            stars = "⭐️" * int(round(score))
            reply_text += f"{i}. <b>{name}</b> — {score:.1f} {stars}\n"

        await message.bot.send_message(
            chat_id=user_id,
            text=reply_text,
            parse_mode="HTML"
        )

    async def handle_feedbacks():
        feedbacks = await db.all_feedbacks()

        
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "all_feedback_msg"),
            parse_mode="HTML"
        )

    async def handle_complaints():
        await message.bot.send_message(
            chat_id=user_id,
            text="",
            # reply_markup=
        )  
        # await state.set_state(st.director.)

    async def handle_pins():
        await message.bot.send_message(
            chat_id=user_id,
            text="",
            # reply_markup=
        )
        # await state.set_state(st.director.)

    handlers = {
        text_back: handle_back,
        text_rating: handle_ratings,
        text_feedback: handle_feedbacks,
        text_complaint: handle_complaints,
        text_pin: handle_pins
    }

    handle = handlers.get(text)

    if handle:
        await handle()
        return
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

##################################################################################################################