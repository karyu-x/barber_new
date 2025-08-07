import asyncio
from aiogram import Router
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
role = "director"

##################################################################################################################

@router.message(st.director.main_menu)
async def main_menu(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
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
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

##################################################################################################################

@router.message(st.director.notifications)
async def notifications(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
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
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

### INPUT TEXT

@router.message(st.director.input_text)
async def input_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
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

    reply_text = cf.get_text(lang, role, "message", "text_accepted_msg").format(message.text)
    await state.update_data(description=message.text)
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
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
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

    await message.bot.send_message(
        chat_id=user_id, 
        text=cf.get_text(lang, "errors", "photo_required_msg")
    )

### INPUT BUTTON

@router.message(st.director.input_button)
async def input_button(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
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
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, "errors", "invalid_button_format"),
            parse_mode="HTML",
            reply_markup=kb_r.notifications(lang)
        )
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
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
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
    handler = handlers.get(message.text)

    if handler:
        await handler()
        return
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

### CONFIRM POST

@router.message(st.director.confirm_post)
async def confirm_post(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text_back = cf.get_text(lang, role, "button", "back")
    text_back_main = cf.get_text(lang, role, "button", "back_main")
    text_confirm = cf.get_text(lang, role, "button", "confirm")
    text_reject = cf.get_text(lang, role, "button", "reject")

    async def handle_back():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "check_post_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.check_post(lang)
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

    async def handle_confirm():
        description = data.get("description")
        photo = data.get("photo")
        buttons = data.get("buttons", [])
        reply_markup = kb_i.post_button(buttons) if buttons else None
        users = db.all_users()
        success, failed = 0, 0
        for tg_id in users:
            try:
                if photo:
                    await message.bot.send_photo(
                        chat_id=tg_id,
                        photo=photo,
                        caption=description,
                        reply_markup=reply_markup,
                        parse_mode="HTML"
                    )
                else:
                    await message.bot.send_message(
                        chat_id=tg_id,
                        text=description,
                        reply_markup=reply_markup,
                        parse_mode="HTML"
                    )
                success += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {tg_id}: {e}")
                failed += 1

        await state.update_data(description=None, photo=None, buttons=None)
        await message.bot.send_message(
            chat_id=user_id,
            text=f"📤 Xabar yuborildi: {success} ta foydalanuvchiga\n❌ Xatolik: {failed} ta"
        )
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)

    async def handle_reject():
        await state.update_data(description=None, photo=None, buttons=None)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "post_cancelled_msg"),
        )
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)

    handlers = {
        text_back: handle_back,
        text_back_main: handle_back_main,
        text_confirm: handle_confirm,
        text_reject: handle_reject
    }
    handler = handlers.get(message.text)

    if handler:
        await handler()
        return
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

##################################################################################################################

@router.message(st.director.bookings)
async def bookings(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
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
        
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

### TODAY BOOKS
@router.message(st.director.today_books)
async def today_books(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "bookings_msg"),
            "reply_markup": kb_r.bookings(lang),
            "state": st.director.bookings
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

    # text_brons = cf.get_text(lang, role, "button", "all_today_bookings")
    # if message.text == text_brons:


### OTHER DAY BOOKS
@router.message(st.director.other_day_books)
async def other_day_books(message: Message, state: FSMContext):
    user_id = message.from_user.id


### CANCEL BOOKS
@router.message(st.director.cancel_books)
async def cancel_books(message: Message, state: FSMContext):
    user_id = message.from_user.id

### RESCHEDULE BOOKS
@router.message(st.director.reschedule_books)
async def reschedule_books(message: Message, state: FSMContext):
    user_id = message.from_user.id


##################################################################################################################

@router.message(st.director.settings)
async def settings(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    buttons = await butt_cf.get_setting_buttons(lang)
    text = message.text.strip()

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

### SERVICE & PRICE
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

    barbers = await db.all_barbers()
    for item in barbers:
        if text == item["name"]:
            await state.update_data(barber_tg_id=item["tg_id"],
                                    barber_name=item["name"])
            await message.bot.send_message(
                chat_id=user_id,
                text=cf.get_text(lang, role, "message", "service_types_msg").format(barber=text),
                parse_mode="HTML",
                reply_markup=await kb_r.barber_types(lang, item["tg_id"])
            )
            await state.set_state(st.director.barber_types)
            return

    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

@router.message(st.director.barber_types)
async def barber_types(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
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

    barber_types = await db.all_barber_types()
    for item in barber_types:
        if text == item["name"]:
            await state.update_data(service_type_id=item["id"],
                                    service_name=text)

            services = await db.all_barber_services()
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

    ## bazaga qo'shish type
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "add_type_succes_msg").format(service_name=text),
        reply_markup=await kb_r.barber_types(lang, barber_id)
    )
    await state.set_state(st.director.barber_types)

@router.message(st.director.delete_type)
async def delete_type(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
    barber_id, barber_name, service_name = data.get("barber_tg_id"), data.get("barber_name"), data.get("service_name")
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
            ## bazaga delete type
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

@router.message(st.director.add_service)
async def add_service(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
    back_actions = {
        # cf.get_text(lang, role, "button", "back"): {
        #     "text": cf.get_text(lang, role, "message", "service_services_msg").format(service_name=),
        #     "reply_markup": await kb_r.barber_services(lang),
        #     "state": st.director.barber_types
        # },
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


@router.message(st.director.delete_sevice)
async def delete_service(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    type_id, service_name = data.get("service_type_id"), data.get("service_name")
    text_confirm = cf.get_text(lang, role, "button", "confirm")
    text_reject = cf.get_text(lang, role, "button", "reject")
    text_back = cf.get_text(lang, role, "button", "back")
    text_main = cf.get_text(lang, role, "button", "back_main")

    async def handle_confirm():
        # baza delete service
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "delete_service_succes_msg"),
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
        services = await db.all_barber_services()
        filtered_services = [s for s in services if s["service_type"] == type_id]

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


@router.message(st.director.barber_services)
async def barber_services(message: Message, state: FSMContext):
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
    
    elif text == cf.get_text(lang, role, "button", "delete_service_type"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "service_type_delete_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.confirm_reject(lang)
        )
        await state.set_state(st.director.delete_type)
        return

    barber_services = await db.all_barber_services()
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


### WORKING HOURS
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


##################################################################################################################

@router.message(st.director.barbers)
async def barbers(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text

    text_back = cf.get_text(lang, role, "button", "back")
    text_add = cf.get_text(lang, role, "button", "add_barber")
    text_delete = cf.get_text(lang, role, "button", "delete_barber")

    async def handle_back():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)

    async def handle_add():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "add_barber_msg"),
            reply_markup=kb_r.add_barber(lang)
        )
        await state.set_state(st.director.add_barber)

    async def handle_delete():
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "delete_barber_msg"),
            reply_markup=await kb_r.delete_barber(lang)
        )
        await state.set_state(st.director.delete_barber)

    async def handle_barber():
        pass

    handlers = {
        text_back: handle_back,
        text_add: handle_add,
        text_delete: handle_delete
    }
    handle = handlers.get(text)

    if handle:
        await handle()
        return
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

### ADD

@router.message(st.director.add_barber)
async def add_barber(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
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
        },
        cf.get_text(lang, role, "button", "add_phone"): {
            "text": cf.get_text(lang, role, "message", "add_phone_msg"),
            "reply_markup": kb_r.back_main(lang),
            "state": st.director.add_phone
        },
        cf.get_text(lang, role, "button", "add_description"): {
            "text": cf.get_text(lang, role, "message", "add_description_msg"),
            "reply_markup": kb_r.back_main(lang),
            "state": st.director.add_description
        },
        cf.get_text(lang, role, "button", "add_photo"): {
            "text": cf.get_text(lang, role, "message", "add_photo_msg"),
            "reply_markup": kb_r.back_main(lang),
            "state": st.director.add_photo
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
    
    if text == cf.get_text(lang, role, "button", "save_barber"):
        barber_name = data.get("barber_name")
        barber_description = data.get("barber_description")
        barber_photo = data.get("barber_photo")
        name_label = cf.get_text(lang, role, "message", "barber_name")
        description_label = cf.get_text(lang, role, "message", "barber_description")
        photo_label = cf.get_text(lang, role, "message", "barber_photo")

        if barber_name:
            msg_text = cf.get_text(lang, role, "message", "save_barber_success_msg")
            # База данных + очистка состояния
            await state.update_data(
                barber_name=None,
                barber_description=None,
                barber_photo=None
            )
            await message.bot.send_message(
                chat_id=user_id,
                text=f"{msg_text}\n\n"
                    f"{name_label} {barber_name}\n"
                    f"{description_label}\n{barber_description or '❌'}\n"
                    f"{photo_label} {'✅' if barber_photo else '❌'}",
                parse_mode="HTML",
                reply_markup=await kb_r.barbers(lang)
            )
            await state.set_state(st.director.barbers)
        else:
            msg_text = cf.get_text(lang, role, "message", "save_barber_fail_msg")
            text_lines = [f"{msg_text}\n"]
            text_lines.append(f"{name_label} ❌")

            if barber_description:
                text_lines.append(f"{description_label}\n{barber_description}")
            else:
                text_lines.append(f"{description_label}\n❌")

            text_lines.append(f"{photo_label} {'✅' if barber_photo else '❌'}")
            full_msg = "\n".join(text_lines)
            await message.bot.send_message(
                chat_id=user_id,
                text=full_msg,
                parse_mode="HTML"
            )
        return
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )


@router.message(st.director.add_phone)
async def add_barber(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "add_barber_msg"),
            "reply_markup": kb_r.add_barber(lang),
            "state": st.director.add_barber
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
    
    await state.update_data(barber_name=text)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "add_name_saved_msg"),
        reply_markup=kb_r.add_barber(lang),
    )
    await state.set_state(st.director.add_barber)

@router.message(st.director.add_description)
async def add_barber(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "add_barber_msg"),
            "reply_markup": kb_r.add_barber(lang),
            "state": st.director.add_barber
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
    
    await state.update_data(barber_description=text)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "add_description_saved_msg"),
        reply_markup=kb_r.add_barber(lang),
    )
    await state.set_state(st.director.add_barber)

@router.message(st.director.add_photo)
async def add_barber(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "add_barber_msg"),
            "reply_markup": kb_r.add_barber(lang),
            "state": st.director.add_barber
        },
        cf.get_text(lang, role, "button", "back_main"): {
            "text": cf.get_text(lang, role, "message", "main_menu_msg"),
            "reply_markup": kb_r.main_menu(lang),
            "state": st.director.main_menu
        }
    }

    if message.text and message.text in back_actions:
        action = back_actions[message.text]
        await message.bot.send_message(
            chat_id=user_id,
            text=action["text"], 
            parse_mode="HTML",
            reply_markup=action["reply_markup"]
        )
        await state.set_state(action["state"])
        return
    
    if not message.photo:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, "errors", "photo_required_msg")
        )
        return
    
    photo = message.photo[-1]
    await state.update_data(barber_photo=photo.file_id)
    
    await state.update_data(barber_name=text)
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "add_photo_saved_msg"),
        reply_markup=kb_r.add_barber(lang),
    )
    await state.set_state(st.director.add_barber)

### DELETE

@router.message(st.director.delete_barber)
async def delete_barber(message: Message, state:FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
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
            parse_mode="HTML",
            reply_markup=action["reply_markup"]
        )
        await state.set_state(action["state"])
        return
    
    barbers = await db.all_barbers()
    if text[4:].strip() in barbers:
        await state.update_data(deletet_barber_name=text)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "delete_barber_confirm_reject_msg").format(barber_name=text),
            parse_mode="HTML",
            reply_markup=kb_r.confirm_reject(lang)
        )
        await state.set_state(st.director.delete_barber_confirm_reject)
        return
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, role, "message", "barber_not_found_msg")
    )

@router.message(st.director.delete_barber_confirm_reject)
async def delete_barber_confirm_reject(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
    back_actions = {
        cf.get_text(lang, role, "button", "back"): {
            "text": cf.get_text(lang, role, "message", "delete_barber_msg"),
            "reply_markup": await kb_r.delete_barber(lang),
            "state": st.director.delete_barber
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
    
    if text == cf.get_text(lang, role, "button", "confirm"):
        # baza
        await state.update_data(delete_barber_name=None)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "barber_deleted_msg"),
            parse_mode="HTML",
            reply_markup=await kb_r.barbers(lang)
        )
        await state.set_state(st.director.barbers)
        return
    
    elif text == cf.get_text(lang, role, "button", "reject"):
        await state.update_data(delete_barber_name=None)
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "cancelled_delete_barber_msg"),
            parse_mode="HTML",
            reply_markup=await kb_r.barbers(lang)
        )
        await state.set_state(st.director.barbers)
        return

    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

##################################################################################################################

@router.message(st.director.admins)
async def admins(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text


##################################################################################################################

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

@router.message(st.director.language)
async def language(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    text = message.text
    text_uz = "🇺🇿 uz"
    text_ru = "🇷🇺 ru"
    text_back = cf.get_text(lang, role, "button", "back")

    if text == text_back:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang)
        )
        await state.set_state(st.director.main_menu)
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
            text=cf.get_text(lang_code, role, "message", "main_menu_msg"),
            parse_mode="HTML",
            reply_markup=kb_r.main_menu(lang=lang_code)
        )
        await state.set_state(st.director.main_menu)
        return
    
    await message.bot.send_message(
        chat_id=user_id,
        text=cf.get_text(lang, "errors", "unknown_command")
    )

##################################################################################################################