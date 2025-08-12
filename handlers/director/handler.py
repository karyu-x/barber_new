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
PHONE_RE = re.compile(r"^\+?998\d{9}$")
TIME_RANGE_RE = re.compile(r"^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}$")

role = "director"

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


##################################################################################################################

@router.message(st.director.main_menu)
async def main_menu(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    buttons = await butt_cf.get_main_buttons(lang)
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

@router.message(st.director.settings)
async def settings(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    buttons = await butt_cf.get_setting_buttons(lang)
    text = message.text.strip()

    if text == cf.get_text(lang, role, "button", "working_hours"):
        reply_text = ""

        await message.bot.send_message(
            chat_id=user_id,
            text=reply_text,
            reply_markup=kb_r.working_hours(lang)
        )
        await state.set_state(st.director.working_hours)
        return

    for key, config in buttons.items():
        if text == cf.get_text(lang, role, "button", key):
            reply_text = cf.get_text(lang, role, "message", config["message"])
            reply_makrup = config["keyboard"]
            await message.bot.send_message(
                chat_id=user_id,
                text=reply_text,
                parse_mode="HTML",
                reply_markup=reply_makrup
            )
            await state.set_state(config["state"])
            return
        
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

########################################################## SERVICE & PRICE ##########################################################
@router.message(st.director.services_prices)
async def services_prices(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text.strip()

    if text == cf.get_text(lang, role, "button", "back"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "settings_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.settings(lang)
        )
        await state.set_state(st.director.settings)
        return
    
    elif text == cf.get_text(lang, role, "button", "back_main"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        return

    barbers = await db.get_barbers_all()
    for item in barbers:
        if text == item["first_name"]:
            await state.update_data(barber_tg_id=item["telegram_id"],
                                    barber_name=item["first_name"])
            barber_types = await db.get_barber_types(item["telegram_id"])
            if barber_types:
                await message.bot.send_message(
                    chat_id=user_id,
                    text=cf.get_text(lang, role, "message", "service_types_msg").format(barber=text),
                    parse_mode="HTML",
                    reply_markup=await kb_r.barber_types(lang, item["telegram_id"])
                )
            else:
                await message.bot.send_message(
                    chat_id=user_id,
                    text=cf.get_text(lang, role, "message", "no_service_type_msg"),
                    reply_markup=await kb_r.barber_types(lang, item["telegram_id"])
                )           
            await state.set_state(st.director.barber_types)
            return

    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

#### BARBER TYPES
@router.message(st.director.barber_types)
async def barber_types(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    barber_id = data.get("barber_tg_id")
    text = message.text
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "services_prices_msg"),
            "reply_markup": await kb_r.services_prices(lang),
            "state": st.director.services_prices
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

    elif text == cf.get_text(lang, role, "button", "add_service_type"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_type_add_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.add_type)
        return

    barber_types = await db.get_barber_types(barber_id)
    for item in barber_types:
        if text == item["name"]:
            await state.update_data(service_type_id=item["id"],
                                    service_type_name=text)

            services = await db.get_barber_services(item["id"])
            filtered_services = [s for s in services if s["service_type"] == item["id"]]

            if filtered_services:
                service_lines = [
                    f"• <b>{s['name']}</b> — {s['price']:,}\n🕒 {s['duration']}\n📝 {s['description']}"
                    for s in filtered_services
                ]
                services_text = "\n\n".join(service_lines)
            else:
                services_text = cf.get_text(lang, role, "message", "no_services_msg")

            reply_text = cf.get_text(lang, role, "message", "service_services_msg").format(service_name=text)
            full_text = f"{reply_text}\n\n{services_text}"

            await message.bot.send_message(
                chat_id=user_id,
                text=full_text,
                parse_mode="HTML",
                reply_markup=await kb_r.barber_services(lang, item["id"])
            )
            await state.set_state(st.director.barber_services)
            return
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

#### ADD TYPE
@router.message(st.director.add_type)
async def add_type(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
    barber_id, barber_name = data.get("barber_tg_id"), data.get("barber_name")
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "service_types_msg").format(barber=barber_name),
            "reply_markup": await kb_r.barber_types(lang, barber_id),
            "state": st.director.barber_types
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

    # TODO: await db.create_barber_type(barber_id, data)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "add_type_succes_msg").format(service_name=text),
        reply_markup=await kb_r.barber_types(lang, barber_id)
    )
    await state.set_state(st.director.barber_types)

#### DELETE TYPE
@router.message(st.director.delete_type)
async def delete_type(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
    barber_id, barber_name, service_name = data.get("barber_tg_id"), data.get("barber_name"), data.get("service_type_name")
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "service_types_msg").format(barber=barber_name),
            "reply_markup": await kb_r.barber_types(lang, barber_id),
            "state": st.director.barber_types
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

    elif text == cf.get_text(lang, role, "button", "confirm"):
        # TODO: await db.delete_barber_type_by_id(type_id)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "delete_type_succes_msg").format(service_name=service_name),
            reply_markup=await kb_r.barber_types(lang, barber_id)
        )
        await state.set_state(st.director.barber_types)
        return
    
    elif text == cf.get_text(lang, role, "button", "reject"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_types_msg").format(barber=barber_name),
            parse_mode="HTML",
            reply_markup=await kb_r.barber_types(lang, barber_id)
        )
        await state.set_state(st.director.barber_types)
        return
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

#### BARBER SERVICES
@router.message(st.director.barber_services)
async def barber_services(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
    barber_id, barber_name, type_id = data.get("barber_tg_id"), data.get("barber_name"), data.get("service_type_id")
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "service_types_msg").format(barber=barber_name),
            "reply_markup": await kb_r.barber_types(lang, barber_id),
            "state": st.director.barber_types
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
    
    elif text == cf.get_text(lang, role, "button", "delete_service_type"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_type_delete_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.confirm_reject(lang)
        )
        await state.set_state(st.director.delete_type)
        return

    elif text == cf.get_text(lang, role, "button", "add_service"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "add_service_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.add_service)
        return

    barber_services = await db.get_barber_services(type_id)
    for item in barber_services:
        if text == item["name"]:
            await state.update_data(service_id=item["id"],
                                    service_name=text)
            reply_text = cf.get_text(lang, role, "message", "service_detail_msg").format(
                description=item["description"],
                duration=item["duration"],
                price=f"{item['price']:,}"
            )
            await message.bot.send_message(
                chat_id=user_id,
                text=(
                    f"<b>{item['name']}</b>\n\n"
                    f"{reply_text}"
                ),
                parse_mode="HTML",
                reply_markup=kb_r.service_detail(lang)
            )
            await state.set_state(st.director.service_detail)
            return
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

#### ADD SERVICE
@router.message(st.director.add_service)
async def add_service(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    type_id, service_name = data.get("service_type_id"), data.get("service_type_name")
    text = message.text
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    async def handle_back():
        filtered_services = await db.get_barber_services(type_id)

        if filtered_services:
            service_lines = [
                f"• <b>{s['name']}</b> — {s['price']:,}\n🕒 {s['duration']}\n📝 {s['description']}"
                for s in filtered_services
            ]
            services_text = "\n\n".join(service_lines)
        else:
            services_text = cf.get_text(lang, role, "message", "no_services_msg")

        reply_text = cf.get_text(lang, role, "message", "service_services_msg").format(service_name=service_name)
        full_text = f"{reply_text}\n\n{services_text}"

        await message.bot.send_message(
            chat_id=user_id,
            text=full_text,
            parse_mode="HTML",
            reply_markup=await kb_r.barber_services(lang)
        )
        await state.set_state(st.director.barber_services)

    async def handle_main():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang),
        )
        await state.set_state(st.director.main_menu)

    handlers = {
        text_back: handle_back,
        text_main: handle_main
    }
    handle = handlers.get(text)

    if handle:
        await handle()
        return

    # TODO: await db.create_barber_service(data)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "add_service_success_msg"),
        reply_markup=await kb_r.barber_services(lang, type_id)
    )
    await state.set_state(st.director.barber_services)

#### DELETE SERVICE
@router.message(st.director.delete_sevice)
async def delete_service(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    type_id, service_name, service_id = data.get("service_type_id"), data.get("service_name"), data.get("service_id")
    text_confirm = cf.get_text(lang, role, "button", "confirm")
    text_reject = cf.get_text(lang, role, "button", "reject")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    async def handle_confirm():
        # TODO: await db.delete_barber_service_by_id(service_id)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "delete_service_success_msg"),
            reply_markup=await kb_r.barber_services(lang, type_id)
        )
        await state.set_state(st.director.barber_services)

    async def handle_reject():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "delete_service_cancel_msg"),
            reply_markup=await kb_r.barber_services(lang, type_id)
        )
        await state.set_state(st.director.barber_services)


    async def handle_back():
        service = await db.get_barber_service_by_id(type_id, service_id)
        if service:
            services_text = cf.get_text(lang, role, "message", "service_detail_msg").format(
                description=service['description'],
                duration=service['duration'],
                price=f"{service['price']:,}"
            )
        else:
            services_text = cf.get_text(lang, role, "message", "no_services_msg")

        full_text = f"<b>{service_name}</b>\n\n{services_text}"

        await message.bot.send_message(
            chat_id=user_id,
            text=full_text,
            parse_mode="HTML",
            reply_markup=kb_r.service_detail(lang)
        )
        await state.set_state(st.director.service_detail)

    async def handle_main():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang),
        )
        await state.set_state(st.director.main_menu)

    handlers = {
        text_confirm: handle_confirm,
        text_reject: handle_reject,
        text_back: handle_back,
        text_main: handle_main
    }

    handle = handlers.get(message.text)

    if handle:
        await handle()
        return
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

#### EDIT SERVICE NAME
@router.message(st.director.edit_service_name)
async def edit_service_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    type_id, service_name, service_id = data.get("service_type_id"), data.get("service_name"), data.get("service_id")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")
    service = await db.get_barber_service_by_id(type_id, service_id)
    if service:
        services_text = cf.get_text(lang, role, "message", "service_detail_msg").format(
            description=service['description'],
            duration=service['duration'],
            price=f"{service['price']:,}"
        )
    else:
        services_text = cf.get_text(lang, role, "message", "no_services_msg")

    full_text = f"<b>{service_name}</b>\n\n{services_text}"

    async def handle_back():
        await message.bot.send_message(
            chat_id=user_id,
            text=full_text,
            parse_mode="HTML",
            reply_markup=kb_r.service_detail(lang)
        )
        await state.set_state(st.director.service_detail)

    async def handle_main():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang),
        )
        await state.set_state(st.director.main_menu)

    handlers = {
        text_back: handle_back,
        text_main: handle_main
    }
    handle = handlers.get(message.text)
    
    if handle:
        await handle()
        return

    # TODO: await db.update_barber_service_by_id(service_id, data)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "edit_service_name_succes_msg")
    )

    full_text = f"<b>{message.text}</b>\n\n{services_text}"

    await message.bot.send_message(
        chat_id=user_id,
        text=full_text,
        parse_mode="HTML",
        reply_markup=kb_r.service_detail(lang)
    )
    await state.set_state(st.director.service_detail)

#### EDIT SERVICE DESCRIPTION
@router.message(st.director.edit_service_description)
async def edit_service_description(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    type_id, service_name, service_id = data.get("service_type_id"), data.get("service_name"), data.get("service_id")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")
    service = await db.get_barber_service_by_id(type_id, service_id)
    if service:
        services_text = cf.get_text(lang, role, "message", "service_detail_msg").format(
            description=service['description'],
            duration=service['duration'],
            price=f"{service['price']:,}"
        )
    else:
        services_text = cf.get_text(lang, role, "message", "no_services_msg")

    full_text = f"<b>{service_name}</b>\n\n{services_text}"

    async def handle_back():
        await message.bot.send_message(
            chat_id=user_id,
            text=full_text,
            parse_mode="HTML",
            reply_markup=kb_r.service_detail(lang)
        )
        await state.set_state(st.director.service_detail)

    async def handle_main():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang),
        )
        await state.set_state(st.director.main_menu)

    handlers = {
        text_back: handle_back,
        text_main: handle_main
    }
    handle = handlers.get(message.text)
    
    if handle:
        await handle()
        return
    
    # TODO: await db.update_barber_service_by_id(service_id, data)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "edit_service_description_success_msg")
    )

    services_text = cf.get_text(lang, role, "message", "service_detail_msg").format(
            description=message.text,
            duration=service['duration'],
            price=f"{service['price']:,}"
        )
    full_text = f"<b>{service_name}</b>\n\n{services_text}"    

    await message.bot.send_message(
        chat_id=user_id,
        text=full_text,
        parse_mode="HTML",
        reply_markup=kb_r.service_detail(lang)
    )
    await state.set_state(st.director.service_detail)

#### EDIT SERVICE DURATION
@router.message(st.director.edit_service_duration)
async def edit_service_duration(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    type_id, service_name, service_id = data.get("service_type_id"), data.get("service_name"), data.get("service_id")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")
    service = await db.get_barber_service_by_id(type_id, service_id)
    if service:
        services_text = cf.get_text(lang, role, "message", "service_detail_msg").format(
            description=service['description'],
            duration=service['duration'],
            price=f"{service['price']:,}"
        )
    else:
        services_text = cf.get_text(lang, role, "message", "no_services_msg")

    full_text = f"<b>{service_name}</b>\n\n{services_text}"

    async def handle_back():
        await message.bot.send_message(
            chat_id=user_id,
            text=full_text,
            parse_mode="HTML",
            reply_markup=kb_r.service_detail(lang)
        )
        await state.set_state(st.director.service_detail)

    async def handle_main():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang),
        )
        await state.set_state(st.director.main_menu)

    handlers = {
        text_back: handle_back,
        text_main: handle_main
    }
    handle = handlers.get(message.text)
    
    if handle:
        await handle()
        return
    
    # TODO: await db.update_barber_service_by_id(service_id, data)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "edit_service_duration_success_msg")
    )

    services_text = cf.get_text(lang, role, "message", "service_detail_msg").format(
            description=service["description"],
            duration=message.text,
            price=f"{service['price']:,}"
        )
    full_text = f"<b>{service_name}</b>\n\n{services_text}"

    await message.bot.send_message(
        chat_id=user_id,
        text=full_text,
        parse_mode="HTML",
        reply_markup=kb_r.service_detail(lang)
    )
    await state.set_state(st.director.service_detail)

#### EDIT SERVICE PRICE
@router.message(st.director.edit_service_price)
async def edit_service_price(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    type_id, service_name, service_id = data.get("service_type_id"), data.get("service_name"), data.get("service_id")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")
    service = await db.get_barber_service_by_id(type_id, service_id)
    if service:
        services_text = cf.get_text(lang, role, "message", "service_detail_msg").format(
            description=service['description'],
            duration=service['duration'],
            price=f"{service['price']:,}"
        )
    else:
        services_text = cf.get_text(lang, role, "message", "no_services_msg")

    full_text = f"<b>{service_name}</b>\n\n{services_text}"

    async def handle_back():
        await message.bot.send_message(
            chat_id=user_id,
            text=full_text,
            parse_mode="HTML",
            reply_markup=kb_r.service_detail(lang)
        )
        await state.set_state(st.director.service_detail)

    async def handle_main():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang),
        )
        await state.set_state(st.director.main_menu)

    handlers = {
        text_back: handle_back,
        text_main: handle_main
    }
    handle = handlers.get(message.text)
    
    if handle:
        await handle()
        return

    # TODO: await db.update_barber_service_by_id(service_id, data)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "edit_service_price_success_msg")
    )

    services_text = cf.get_text(lang, role, "message", "service_detail_msg").format(
            description=service["description"],
            duration=service['duration'],
            price=message.text
        )
    full_text = f"<b>{service_name}</b>\n\n{services_text}"

    await message.bot.send_message(
        chat_id=user_id,
        text=full_text,
        parse_mode="HTML",
        reply_markup=kb_r.service_detail(lang)
    )
    await state.set_state(st.director.service_detail)

#### SERVICE DETAIL
@router.message(st.director.service_detail)
async def service_detail(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    type_id, service_name = data.get("service_type_id"), data.get("service_type_name")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")
    text_delete = cf.get_text(lang, role, "button", "delete_service")
    text_name = cf.get_text(lang, role, "button", "edit_service_name")
    text_description = cf.get_text(lang, role, "button", "edit_service_description")
    text_duration = cf.get_text(lang, role, "button", "edit_service_duration")
    text_price = cf.get_text(lang, role, "button", "edit_service_price")

    async def handle_name():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "edit_service_name_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_service_name)

    async def handle_description():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "edit_service_description_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_service_description)

    async def handle_duration():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "edit_service_duration_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_service_duration)

    async def handle_price():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "edit_service_price_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_service_price)

    async def handle_back():
        filtered_services = await db.get_barber_services(type_id)

        if filtered_services:
            service_lines = [
                f"• <b>{s['name']}</b> — {s['price']:,}\n🕒 {s['duration']}\n📝 {s['description']}"
                for s in filtered_services
            ]
            services_text = "\n\n".join(service_lines)
        else:
            services_text = cf.get_text(lang, role, "message", "no_services_msg")

        reply_text = cf.get_text(lang, role, "message", "service_services_msg").format(service_name=service_name)
        full_text = f"{reply_text}\n\n{services_text}"

        await message.bot.send_message(
            chat_id=user_id,
            text=full_text,
            parse_mode="HTML",
            reply_markup=await kb_r.barber_services(lang, type_id)
        )
        await state.set_state(st.director.barber_services)

    async def handle_main():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang),
        )
        await state.set_state(st.director.main_menu)

    async def handle_delete():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "delete_service_msg"),
            reply_markup=kb_r.confirm_reject(lang)
        )
        await state.set_state(st.director.delete_sevice)

    handlers = {
        text_back: handle_back,
        text_main: handle_main,
        text_delete: handle_delete,
        text_name: handle_name,
        text_description: handle_description,
        text_duration: handle_duration,
        text_price: handle_price
    }
    handle = handlers.get(message.text)

    if handle:
        await handle()
        return
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )
##################################################### SERVICE & PRICE #######################################################

########################################################## BARBERS ##########################################################
@router.message(st.director.barbers)
async def barbers(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text.strip()
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")
    text_add = cf.get_text(lang, role, "button", "add_barber")

    if text == text_back:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "settings_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.settings(lang)
        )
        await state.set_state(st.director.settings)
        return

    if text == text_main:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        return

    if text == text_add:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "add_barber_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.add_barber)
        return

    barbers = await db.get_barbers_all()
    for barber in barbers:
        if text.lower() == barber["first_name"].strip().lower():
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
            await state.update_data(barber_tg_id=barber["telegram_id"],
                                    barber_name=barber["first_name"])

            if barber["photo"]:
                await message.bot.send_photo(
                    chat_id=user_id,
                    photo=barber["photo"],
                    caption=text_reply,
                    parse_mode="HTML",
                    reply_markup=kb_r.barber_detail(lang)
                )
            else:
                await message.bot.send_message(
                    chat_id=user_id,
                    text=text_reply,
                    parse_mode="HTML",
                    reply_markup=kb_r.barber_detail(lang)
                )

            await state.set_state(st.director.barber_detail)
            return

    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

### ADD
@router.message(st.director.add_barber)
async def add_barber(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")

    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "barbers_msg"),
            "reply_markup": await kb_r.barbers(lang),
            "state": st.director.barbers
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
            reply_markup=action["reply_markup"]
        )
        await state.set_state(action["state"])
        return

    phone = text.replace(" ", "").replace("-", "")
    if not re.fullmatch(r"(\+?998\d{9})", phone):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, "errors", "invalid_phone_number_msg")
        )
        return

    # TODO: Добавить сохранение барбера в базу или другой логике
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "add_barber_success_msg").format(phone=phone),
        reply_markup=await kb_r.barbers(lang)
    )
    await state.set_state(st.director.barbers)

### BARBER DETAIL
@router.message(st.director.barber_detail)
async def barber_detail(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")
    text_delete = cf.get_text(lang, role, "button", "delete_barber")
    text_phone = cf.get_text(lang, role, "button", "edit_barber_phone")
    text_description = cf.get_text(lang, role, "button", "edit_barber_description")
    text_photo = cf.get_text(lang, role, "button", "edit_barber_photo")
    text_start_end = cf.get_text(lang, role, "button", "edit_barber_time")

    if text == text_back:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "barbers_msg"),
            parse_mode="HTML",
            reply_markup=await kb_r.barbers(lang)
        )
        await state.set_state(st.director.barbers)
        return

    if text == text_main:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        return

    if text == text_delete:
        barber_name = data.get("barber_name")
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "delete_barber_confirm_reject_msg").format(barber_name=barber_name),
            parse_mode="HTML",
            reply_markup=kb_r.confirm_reject(lang)
        )
        await state.set_state(st.director.delete_barber)
        return

    if text == text_phone:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "edit_barber_phone_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_barber_phone)
        return

    if text == text_description:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "edit_barber_description_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_barber_description)
        return

    if text == text_photo:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "edit_barber_photo_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_barber_photo)
        return

    if text == text_start_end:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "edit_barber_time_msg"),
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_barber_time)
        return

    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "invalid_command_msg")
    )

### EDIT BARBER PHONE
@router.message(st.director.edit_barber_phone)
async def edit_barber_phone(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_main:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        return

    if text == text_back:
        telegram_id = data.get("barber_tg_id")
        barber = await db.get_barber_by_id(telegram_id)
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
        await message.bot.send_message(
            chat_id=user_id,
            text=text_reply,
            parse_mode="HTML",
            reply_markup=kb_r.barber_detail(lang)
        )
        await state.set_state(st.director.barber_detail)
        return

    if not re.match(r"^\+?998\d{9}$", text):
        error_msg = cf.get_text(lang, "errors", "invalid_phone_number_msg")
        await message.bot.send_message(user_id, error_msg)
        return

    # TODO: await db.update_barber_by_id(telegram_id, data)
    await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "edit_phone_success_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.barber_detail(lang)
        )
    await state.set_state(st.director.barber_detail)

### EDIT BARBER DESCRIPTION
@router.message(st.director.edit_barber_description)
async def edit_barber_description(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_main:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        return

    if text == text_back:
        telegram_id = data.get("barber_tg_id")
        barber = await db.get_barber_by_id(telegram_id)
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
        await message.bot.send_message(
            chat_id=user_id, 
            text=text_reply, 
            parse_mode="HTML", 
            reply_markup=kb_r.barber_detail(lang)
        )
        await state.set_state(st.director.barber_detail)
        return

    # TODO: await db.update_barber_by_id(telegram_id, data)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "edit_description_success_msg"),
        parse_mode="HTML",
        reply_markup=kb_r.barber_detail(lang)
    )
    await state.set_state(st.director.barber_detail)

### EDIT BARBER PHOTO
@router.message(st.director.edit_barber_photo)
async def edit_barber_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text_main = cf.get_text(lang, role, "button", "back_main")
    text_back = cf.get_text(lang, role, "button", "back")

    if message.text and message.text.strip() == text_main:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        return

    if message.text and message.text.strip() == text_back:
        telegram_id = data.get("barber_tg_id")
        barber = await db.get_barber_by_id(telegram_id)
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
        await message.bot.send_message(
            chat_id=user_id, 
            text=text_reply, 
            parse_mode="HTML", 
            reply_markup=kb_r.barber_detail(lang)
        )
        await state.set_state(st.director.barber_detail)
        return

    if not message.photo:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, "errors", "photo_required_msg"), 
            reply_markup=kb_r.back_main(lang)
        )
        return

    # TODO: await db.update_barber_by_id(telegram_id, data)
    photo_id = message.photo[-1].file_id
    telegram_id = data.get("barber_tg_id")

    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "edit_photo_success_msg"),
        reply_markup=kb_r.barber_detail(lang)
    )
    await state.set_state(st.director.barber_detail)

### EDIT BARBER TIME
@router.message(st.director.edit_barber_time)
async def edit_barber_time(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_main:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        return

    if text == text_back:
        telegram_id = data.get("barber_tg_id")
        barber = await db.get_barber_by_id(telegram_id)
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
        await message.bot.send_message(
            chat_id=user_id, 
            text=text_reply, 
            parse_mode="HTML", 
            reply_markup=kb_r.barber_detail(lang)
        )
        await state.set_state(st.director.barber_detail)
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

    # TODO: await db.update_barber_by_id(telegram_id, data)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "edit_time_success_msg"),
        parse_mode="HTML",
        reply_markup=kb_r.barber_detail(lang)
    )
    await state.set_state(st.director.barber_detail)


### DELETE
@router.message(st.director.delete_barber)
async def delete_barber(message: Message, state:FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")
    
    if text == text_back:
        telegram_id = data.get("barber_tg_id")
        barber = await db.get_barber_by_id(telegram_id)
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
        await message.bot.send_message(
            chat_id=user_id, 
            text=text_reply, 
            parse_mode="HTML", 
            reply_markup=kb_r.barber_detail(lang)
        )
        await state.set_state(st.director.barber_detail)
        return

    if text == text_main:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        return

    if text == cf.get_text(lang, role, "button", "confirm"):
        # TODO: await db.delete_barber_by_id(telegram_id)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "barber_deleted_msg"),
            parse_mode="HTML",
            reply_markup=await kb_r.barbers(lang)
        )
        await state.set_state(st.director.barbers)
        return
    
    if text == cf.get_text(lang, role, "button", "reject"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "cancelled_delete_admin_msg"),
            parse_mode="HTML",
            reply_markup=await kb_r.admins(lang)
        )
        await state.set_state(st.director.admins)
        return

    await send_error(message, state)

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

@router.message(st.director.admins)
async def admins(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")
    text_add = cf.get_text(lang, role, "button", "add_admin")

    if text == text_back:
        await handle_back_navigation(message, state, st.director.settings, "settings_msg", kb_r.settings(lang))
        return
    
    elif text == text_main:
        await handle_back_navigation(message, state, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return

    elif text == text_add:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "add_admin_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.add_admin)
        return

    admins = await db.get_admins_all()
    q = text.lower()
    for item in admins:
        name = (item.get("first_name") or "").strip()
        if name.lower() == q:
            await state.update_data(
                admin_telegram_id=item.get("telegram_id"),
                admin_name=name
            )
            admin_id = item.get("telegram_id")
            button_ids = cf.get_admin_buttons(admin_id) or []
            but_names = [butt_cf.button_title(lang, role, bid) for bid in button_ids]
            buttons_str = ", ".join(but_names) if but_names else "—"
            msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
                name=item.get("first_name") or "",
                phone=item.get("phone_number") or "",
                buttons=buttons_str
            )
            await message.bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=kb_r.admin_detail(lang))
            await state.set_state(st.director.admin_detail)
            return

    await send_error(message, state)
    
@router.message(st.director.add_admin)
async def add_admin(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        await handle_back_navigation(message, state, st.director.admins, "admins_msg", await kb_r.admins(lang))
        return
    
    elif text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return

    phone = text.replace(" ", "").replace("-", "")
    if not re.fullmatch(r"(\+?998\d{9})", phone):
        await send_error(message, state, "invalid_phone_number_msg")
        return

    # TODO: Добавить сохранение админа в базу или другой логике
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "add_admin_success_msg").format(phone=phone),
        parse_mode="HTML",
        reply_markup=await kb_r.admins(lang)
    )
    await state.set_state(st.director.admins)    

@router.message(st.director.admin_detail)
async def admin_detail(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    name = data.get("admin_name")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")
    text_delete = cf.get_text(lang, role, "button", "delete_admin")
    text_phone = cf.get_text(lang, role, "button", "edit_admin_phone")
    text_button = cf.get_text(lang, role, "button", "edit_admin_button")

    if text == text_back:
        await handle_back_navigation(message, state, st.director.admins, "admins_msg", await kb_r.admins(lang))
        return
    
    elif text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return

    elif text == text_delete:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "delete_admin_confirm_reject_msg").format(name=name),
            parse_mode="HTML",
            reply_markup=kb_r.confirm_reject(lang)
        )
        await state.set_state(st.director.delete_admin)
        return 

    elif text == text_phone:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "edit_admin_phone_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.back_main(lang)
        )
        await state.set_state(st.director.edit_admin_phone)
        return

    elif text == text_button:
        admin_id = data.get("admin_telegram_id")
        current = set(cf.get_admin_buttons(admin_id))
        await state.update_data(_edit_admin_buttons=list(current))
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=cf.get_text(lang, role, "message", "edit_admin_button_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.ReplyKeyboardRemove()
        )
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=cf.get_text(lang, role, "message", "edit_buttons_choice_msg"),
            reply_markup=kb_i.build_admin_buttons_editor(lang, role, current)
        )
        await state.set_state(st.director.edit_admin_button)
        return

    await send_error(message, state)

@router.message(st.director.edit_admin_phone)
async def edit_admin_phone(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    admin_id = data.get("admin_telegram_id")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        admin = await db.get_admin_by_id(admin_id)
        admin_id = admin.get("telegram_id")
        button_ids = cf.get_admin_buttons(admin_id) or []
        but_names = [butt_cf.button_title(lang, role, bid) for bid in button_ids]
        buttons_str = ", ".join(but_names) if but_names else "—"

        msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
            name=admin.get("first_name") or "",
            phone=admin.get("phone_number") or "",
            buttons=buttons_str
        )
        await handle_back_navigation(message, state, st.director.admin_detail, msg, kb_r.admin_detail(lang))
        return
    
    elif text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return
    
    phone = text.replace(" ", "").replace("-", "")
    if not re.fullmatch(r"(\+?998\d{9})", phone):
        await send_error(message, state, "invalid_phone_number_msg")
        return

    # TODO: Добавить изменение админа в базу или другой логике
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "edit_phone_success_msg").format(phone=phone),
        parse_mode="HTML",
        reply_markup=kb_r.admin_detail(lang)
    )
    await state.set_state(st.director.admin_detail)


@router.callback_query(F.data.startswith("adm_btn:"), st.director.edit_admin_button)
async def admin_buttons_callbacks(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    admin_id = data.get("admin_telegram_id")
    admin = await db.get_admin_by_id(admin_id)
    selected = set(data.get("_edit_admin_buttons") or [])
    action = call.data

    if action == "adm_btn:back":
        await call.message.edit_reply_markup(reply_markup=None)
        await call.answer()
        button_ids = cf.get_admin_buttons(admin_id) or []
        but_names = [butt_cf.button_title(lang, role, bid) for bid in button_ids]
        buttons_str = ", ".join(but_names) if but_names else "—"

        msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
            name=admin.get("first_name") or "",
            phone=admin.get("phone_number") or "",
            buttons=buttons_str
        )
        await call.message.answer(msg, parse_mode="HTML", reply_markup=kb_r.admin_detail(lang))
        await state.set_state(st.director.admin_detail)
        return

    if action == "adm_btn:save":
        cf.set_admin_buttons(admin_id, sorted(selected))
        await call.message.edit_reply_markup(reply_markup=None)
        await call.answer(cf.get_text(lang, role, "message", "edit_admin_button_success_msg"), show_alert=True)
        button_ids = cf.get_admin_buttons(admin_id) or []
        but_names = [butt_cf.button_title(lang, role, bid) for bid in button_ids]
        buttons_str = ", ".join(but_names) if but_names else "—"

        msg = cf.get_text(lang, role, "message", "admin_info_msg").format(
            name=admin.get("first_name") or "",
            phone=admin.get("phone_number") or "",
            buttons=buttons_str
        )
        await call.message.answer(msg, parse_mode="HTML", reply_markup=kb_r.admin_detail(lang))
        await state.set_state(st.director.admin_detail)
        return

    if action.startswith("adm_btn:toggle:"):
        try:
            _, _, bid = action.split(":", 2)
        except ValueError:
            await call.answer("Ошибка формата callback_data", show_alert=True)
            return

        if bid in selected:
            selected.remove(bid)
        else:
            selected.add(bid)

        await state.update_data(_edit_admin_buttons=list(selected))

        new_kb = kb_i.build_admin_buttons_editor(lang, role, selected)
        await call.message.edit_reply_markup(reply_markup=new_kb)

        await call.answer()


@router.message(st.director.delete_admin)
async def delete_admin(message: Message, state: FSMContext):
    user_id, data, lang, text = await get_user_context(message, state)
    admin_id = data.get("admin_telegram_id")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_back:
        admin = await db.get_admin_by_id(admin_id)
        buttons = cf.get_admin_buttons(admin_id)
        msg = (
            cf.get_text(lang, role, "message", "admin_info_msg").format(
                    name=admin.get("first_name") or "",
                    phone=admin.get("phone_number") or "",
                    buttons=buttons or ""
                )   
        )
        await handle_back_navigation(message, state, st.director.admin_detail, msg, kb_r.admin_detail(lang))
        return

    elif text == text_main:
        await handle_back_navigation(message, text, st.director.main_menu, "main_menu_msg", kb_r.main_menu(lang))
        return

    elif text == cf.get_text(lang, role, "button", "confirm"):
        # TODO: await db.delete_admin_by_id(telegram_id)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "admin_deleted_msg"),
            parse_mode="HTML",
            reply_markup=await kb_r.admins(lang)
        )
        await state.set_state(st.director.admins)
        return
    
    elif text == cf.get_text(lang, role, "button", "reject"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "cancelled_delete_admin_msg"),
            parse_mode="HTML",
            reply_markup=await kb_r.admins(lang)
        )
        await state.set_state(st.director.admins)
        return

    await send_error(message, state)

########################################################## LANGUAGE ##########################################################

@router.message(st.director.language)
async def language(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
    text_uz = "🇺🇿 uz"
    text_ru = "🇷🇺 ru"
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    if text == text_main:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
        return
    
    if text == text_back:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "settings_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.settings(lang)
        )
        await state.set_state(st.director.settings)
        return
    
    if text in [text_uz, text_ru]:
        lang_code = "🇺🇿 uz" if text == text_uz else "🇷🇺 ru"
        await state.update_data(lang=lang_code)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang_code, role, "message", "language_selected_msg")
        )
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang_code, role, "message", "settings_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.settings(lang=lang_code)
        )
        await state.set_state(st.director.settings)
        return
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

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