from datetime import datetime, timedelta, time as dtime, timezone
import datetime as dt

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatAction
from aiogram.types import Message, ReplyKeyboardRemove

from databases import database as db
from states import state as st
from configs import functions as cf
from configs.survey_storage import add_pending
from keyboards import reply as kb

user_router = Router()
router = user_router

role = "client"

def next_day_utc_15(end_time_utc_iso: str) -> str:
    end_dt = datetime.fromisoformat(end_time_utc_iso.replace("Z", "+00:00"))
    target = datetime.combine((end_dt.date() + timedelta(days=1)), dtime(15, 0), tzinfo=timezone.utc)
    return target.isoformat(timespec="seconds").replace("+00:00", "Z")


def get_barber_info(lang: str, barber: dict, schedule: list[dict]) -> str:
    name = barber.get("first_name", "N/A")
    phone = barber.get("phone_number", "❌")
    desc = barber.get("description") or "❌"

    days_uz = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

    days = days_uz if lang == "🇺🇿 uz" else days_ru

    schedule_text = ""
    for item in sorted(schedule, key=lambda x: x["weekday"]):
        day_name = days[item["weekday"]]
        from_hour = item["from_hour"][:-3]
        to_hour = item["to_hour"][:-3]
        schedule_text += f"• {day_name}: {from_hour} - {to_hour}\n"

    if lang == "🇺🇿 uz":
        text = (
            f"👤 <b>Usta haqida ma'lumot</b>\n\n"
            f"👨‍🦱 Ism: {name}\n"
            f"📞 Telefon: {phone}\n"
            f"ℹ️ Tavsif: {desc}\n\n"
            f"🗓 <b>Ish jadvali</b>\n{schedule_text}"
        )
    else:
        text = (
            f"👤 <b>Информация о барбере</b>\n\n"
            f"👨‍🦱 Имя: {name}\n"
            f"📞 Телефон: {phone}\n"
            f"ℹ️ Описание: {desc}\n\n"
            f"🗓 <b>Рабочее расписание</b>\n{schedule_text}"
        )

    return text


def get_type_info(lang: str, services: list[dict]) -> str:
    if not services:
        return "❌ Hozircha xizmatlar yo‘q" if lang == "🇺🇿 uz" else "❌ Пока нет услуг"

    text = "💈 <b>Xizmatlar ro‘yxati</b>\n\n" if lang == "🇺🇿 uz" else "💈 <b>Список услуг</b>\n\n"

    for s in services:
        name = s.get("name", "❌")
        desc = s.get("description", "❌")
        duration = s.get("duration", "00:00:00")[:-3]
        price = s.get("price", 0)

        if lang == "🇺🇿 uz":
            text += (
                f"✂️ <b>{name}</b>\n"
                f"   📝 {desc}\n"
                f"   ⏱ Davomiyligi: {duration}\n"
                f"   💵 Narxi: {price:,} so‘m\n\n"
            )
        else:
            text += (
                f"✂️ <b>{name}</b>\n"
                f"   📝 {desc}\n"
                f"   ⏱ Длительность: {duration}\n"
                f"   💵 Цена: {price:,} сум\n\n"
            )

    return text


def get_service_info(lang: str, service: dict) -> str:
    name = service.get("name", "❌")
    desc = service.get("description", "❌")
    duration = service.get("duration", "00:00:00")[:-3]
    price = service.get("price", 0)

    if lang == "🇺🇿 uz":
        text = (
            f"✂️ <b>{name}</b>\n\n"
            f"📝 Tavsif: {desc}\n"
            f"⏱ Davomiyligi: {duration}\n"
            f"💵 Narxi: {price:,} so‘m\n"
        )
    else:
        text = (
            f"✂️ <b>{name}</b>\n\n"
            f"📝 Описание: {desc}\n"
            f"⏱ Длительность: {duration}\n"
            f"💵 Цена: {price:,} сум\n"
        )

    return text
    


@router.message(st.user.language)
async def ask_phone(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text in ["🇺🇿 uz", "🇷🇺 ru"]:
        await state.update_data(lang=message.text)
        data = await state.get_data()
        lang = data['lang']
        await message.bot.send_message(chat_id=user_id,text=cf.get_text(lang, role,'message_text', 'phone'), reply_markup=kb.ask_phone(lang))
        await state.set_state(st.user.phone)

    else:
        await message.bot.send_message(chat_id=user_id,text=cf.get_text("🇺🇿 uz", 'errors', 'error_lang'))


@router.message(st.user.phone)
async def check_phone(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data['lang']
    if message.contact:
        await state.update_data(phone=message.contact.phone_number)
        await message.bot.send_message(chat_id=user_id,text=cf.get_text(lang, role,'message_text', 'name'), reply_markup=ReplyKeyboardRemove())
        await state.set_state(st.user.fio)
    else:
        text = message.text
        if message.text.startswith("+998") and len(text) == 13 and text[1:].isdigit():
            await state.update_data(phone=message.text)
            await message.bot.send_message(chat_id=user_id,text=cf.get_text(lang, role,'message_text', 'name'), reply_markup=ReplyKeyboardRemove())
            await state.set_state(st.user.fio)
        else:
            await message.bot.send_message(chat_id=user_id,text=cf.get_text(lang, role,'message_text', 'error_phone'))



@router.message(st.user.fio)
async def fio_user(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data['lang']
    ok = True
    for i in message.text:
        if not i.isalpha():
            await message.bot.send_message(chat_id=user_id,text=cf.get_text(lang, role,'message_text', 'error_name'))
            ok = False
            break
    if ok:
        await state.update_data(user_name=message.text)
        msg_text = (
            f"{cf.get_text(lang, role,'message_text', 'confirmed_userinfo')}\n"
            f"{cf.get_text(lang, role,'message_text', 'conf_phone')} {data['phone']}\n"
            f"{cf.get_text(lang, role,'message_text', 'conf_name')} {message.text}\n"
        )

        await message.bot.send_message(chat_id=user_id,text=msg_text, reply_markup=kb.conf(lang))
        await state.set_state(st.user.conf)



@router.message(st.user.conf)
async def check_conf_customer(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data['lang']
    user_response = message.text

    if user_response == cf.get_text(lang, role, "buttons", "confirm"):
        user = await db.create_user(
            telegram_id=user_id,
            phone=data['phone'],
            first_name=data['user_name'],
            language=lang
        )
        if user:
            my_infos = await db.get_user_by_id(telegram_id=user_id)
            await state.update_data(my_infos=my_infos)
            await message.answer(
                text=cf.get_text(lang, role, 'message_text', 'menu'),
                reply_markup=kb.us_main_menu(lang, my_infos.get("roles"))
            )
            await state.set_state(st.user.main_menu)

    elif user_response == cf.get_text(lang, role, "buttons", "rejected"):
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.translations['start'],
            reply_markup=kb.start_key(),
            parse_mode='HTML'
        )
        await state.set_state(st.user.language)

    else:
        await message.bot.send_message(
            chat_id=user_id,
            text=cf.get_text(lang, 'errors', 'error_conf')
        )


@router.message(st.user.main_menu)
async def menu_check_button(message: Message, state: FSMContext):
    try:
        role = "client"
        user_id = message.from_user.id
        data = await state.get_data()
        my_infos = data.get("my_infos") or {}
        lang = data.get("lang") or "🇺🇿 uz"
        roles = set(my_infos.get("roles") or [])  

        barber_menu = "💈 Меню барбера"
        director_menu = "🛠 Меню директора"
        admin_menu = "👔 Меню менеджера"

        if message.text == cf.get_text(lang, role,"buttons", "booking"):
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            reply_markup, _ = await kb.barber_name(lang)
            await message.answer(text=cf.get_text(lang, role,'message_text', 'barber_name'), reply_markup=reply_markup)
            await state.set_state(st.user.barber_name)
            
        elif message.text == cf.get_text(lang, role,"buttons", "change_lang"):
            await message.answer(text=cf.get_text(lang, role,'message_text', 'change_language'), reply_markup=kb.language(lang))
            await state.set_state(st.user.change_language)

        elif message.text == cf.get_text(lang, role,"buttons", "booking_history"):
            booking_history = await db.user_booking_history(user_id)
            if booking_history:
                await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
                await message.answer(text=cf.get_text(lang, role,'message_text', 'booking_history'), reply_markup=await kb.booking_history(lang, user_id))
                await state.set_state(st.user.booking_history)

            else:
                await message.answer(text=cf.get_text(lang, role,'message_text', 'no_booking_history'))

        elif message.text == cf.get_text(lang, role,"buttons", "contact_menu"):
            contact = cf.get_info_project().get("project_contact", {})
            await message.answer(
                text=f"📞 {contact['contact']}\n✂️ {contact['barber_shop']}")

        elif message.text == cf.get_text(lang, role,"buttons", "location"):
            location = cf.get_info_project().get("project_location", {})
            await message.bot.send_location(chat_id=user_id, latitude=location["latitude"], longitude=location["longitude"])
            await message.answer(text=f"📍 {location['address']}")

        elif message.text == cf.get_text(lang, role,"buttons", "price_list"):
            price_list = cf.get_info_project().get("project_price_list", {})
            await message.answer(text=price_list["message"])

        else:

            if message.text == barber_menu and 1 in roles:
                role = "barber"
                await message.answer(
                    text=cf.get_text(lang, role, "message", "main_menu_msg"),
                    reply_markup=kb.br_main_menu(lang)
                )
                await state.set_state(st.barber.main_menu)
                return

            elif message.text == director_menu and 3 in roles:
                role = "director"
                await message.answer(
                    text=cf.get_text(lang, role, "message", "main_menu_msg"),
                    reply_markup=kb.dr_main_menu(lang)
                )
                await state.set_state(st.director.main_menu)
                return

            elif message.text == admin_menu and 4 in roles:
                role = "director"
                if kb.ad_main_menu(lang, user_id) is not None:
                    await message.answer(
                        text=cf.get_text(lang, role, "message", "main_menu_msg"),
                        reply_markup=kb.ad_main_menu(lang, telegram_id=user_id)
                    )
                    await state.set_state(st.admin.main_menu)
                    return
                else:
                    await message.answer(text=cf.get_text(lang, role, "message", "main_menu_msg"))

    except Exception as e:
        print(f"Error:{e}")



@router.message(st.user.change_language)
async def change_language(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    my_infos = data.get("my_infos")
    lang = data['lang']

    if message.text == cf.get_text(lang, role,"buttons", "back"):
        await message.answer(text=cf.get_text(lang, role,'message_text', 'menu'), reply_markup=kb.us_main_menu(lang, my_infos.get("roles")))
        await state.set_state(st.user.main_menu)
        return

    elif message.text in ["🇺🇿 uz", "🇷🇺 ru"]:
        await state.update_data(lang=message.text)
        await db.update_user_by_id(my_infos["id"], {"language": "uz" if message.text == "🇺🇿 uz" else "ru"})
        await message.answer(text=cf.get_text(message.text, role, 'message_text', 'menu'), reply_markup=kb.us_main_menu(message.text, my_infos.get("roles")))
        await state.set_state(st.user.main_menu)

    else:
        await message.answer(cf.get_text(lang, "errors", "unknown_command"))


@router.message(st.user.booking_history)
async def booking_history(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    my_infos = data.get("my_infos")
    lang = data['lang']
    booking_times = await db.user_booking_history(tg_id=user_id)

    if message.text == cf.get_text(lang, role,"buttons", "back"):
        await message.answer(text=cf.get_text(lang, role,'message_text', 'menu'), reply_markup=kb.us_main_menu(lang, my_infos.get("roles")))
        await state.set_state(st.user.main_menu)

    else:
        for i in booking_times:
            day = i["start_time"].split("T")[0]
            time = i["start_time"].split("T")[1][:5]
            if message.text == f"{day} {time}":
                start_time = datetime.strptime(i["start_time"], "%Y-%m-%dT%H:%M:%S")
                time = start_time.strftime("%d-%m-%Y %H:%M")
                barber = await db.get_user_by_id(id=i["barber"])
                service = await db.get_barber_service_by_id(service_id=i["service"])
                booking_msg = (
                    f"📅 <b>Vaqt/Время</b>: {time}\n"
                    f"👤 <b>Barber/Барбер</b>: {barber['first_name']}\n"
                    f"✂️ <b>Xizmat/Услуга</b>: {service['name']}\n"
                    f"💰 <b>Narxi/Цена</b>: {service['price']} UZS\n"
                )
                await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
                await message.answer(text=booking_msg, parse_mode="HTML")
                break


@router.message(st.user.barber_name)
async def barber_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    my_infos = data.get("my_infos")
    lang = data.get("lang")

    _, barbers = await kb.barber_name(lang)

    if message.text == cf.get_text(lang, role, "buttons", "back"):
        await message.answer(text=cf.get_text(lang, role,'message_text', 'menu'), reply_markup=kb.us_main_menu(lang, my_infos.get("roles")))
        await state.set_state(st.user.main_menu)

    elif message.text in barbers:
        barber = await db.get_user_by_id(telegram_id=barbers[message.text])
        schedule = await db.get_barber_hours_by_telegram(barber.get("telegram_id"))
        reply_markup, _ = await kb.types_button(lang, barber.get("telegram_id"))
        barber["schedule"] = schedule
        await state.update_data(barber=barber)
        await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        barber_info = get_barber_info(lang, barber, schedule)

        if barber.get("photo"):
            await message.answer_photo(photo=barber.get("photo"), caption=barber_info, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await message.answer(text=barber_info, parse_mode="HTML", reply_markup=reply_markup)

        await message.answer(text=cf.get_text(lang, role,'message_text', 'service_type'))
        await state.set_state(st.user.check_service_type)

    else:
        await message.answer(text=cf.get_text(lang, "errors", "unknown_command"))


@router.message(st.user.check_service_type)
async def check_service_type(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    barber = data.get("barber")
    lang = data.get("lang")

    reply_markup, type_with_id = await kb.types_button(lang, barber.get("telegram_id"))

    if message.text == cf.get_text(lang, role, "buttons", "back"):
        reply_markup, _ = await kb.barber_name(lang)
        await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        await message.answer(text=cf.get_text(lang, role,'message_text', 'barber_name'), reply_markup=reply_markup)
        await state.set_state(st.user.barber_name)
    
    elif message.text in type_with_id:
        type_id = type_with_id[message.text]
        type_about = await db.get_barber_type_by_id(type_id)
        type_services = await db.get_barber_services(type_id)
        reply_markup, _ = await kb.services_button(lang, type_id)
        type_info = get_type_info(lang, type_services)
        await state.update_data(type=type_about, type_services=type_services)
        await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        await message.answer(type_info, parse_mode="HTML", reply_markup=reply_markup)
        await message.answer(text=cf.get_text(lang, role,'message_text', 'optionforservices'))
        await state.set_state(st.user.date)

    else:
        await message.answer(text=cf.get_text(lang, "errors", "unknown_command"))


@router.message(st.user.date)
async def date(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    barber = data.get("barber")
    type_info = data.get("type")
    lang = data.get("lang")

    reply_markup, services = await kb.services_button(lang, type_id=type_info.get("id"))

    if message.text == cf.get_text(lang, role, "buttons", "back"):
        reply_markup, _ = await kb.types_button(lang, barber.get("telegram_id"))
        await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

        barber_info = get_barber_info(lang, barber, barber.get("schedule"))

        if barber.get("photo"):
            await message.answer_photo(photo=barber.get("photo"), caption=barber_info, parse_mode="HTML")
        else:
            await message.answer(text=barber_info, parse_mode="HTML")

        await message.answer(text=cf.get_text(lang, role,'message_text', 'service_type'), reply_markup=reply_markup)
        await state.set_state(st.user.check_service_type)

    elif message.text in services:
        service_id = services[message.text]
        service = await db.get_barber_service_by_id(service_id)
        service_info = get_service_info(lang, service)
        await state.update_data(service=service)
        await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        await message.answer(service_info, parse_mode="HTML",reply_markup=await kb.date(lang))
        await message.answer(text=cf.get_text(lang, role,'message_text', 'select_date'))
        await state.set_state(st.user.time)

    else:
        await message.answer(text=cf.get_text(lang, "errors", "unknown_command"))


@router.message(st.user.time)
async def time(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    barber = data.get("barber")
    type = data.get("type")
    type_services = data.get("type_services")
    service = data.get("service")
    lang = data.get("lang")

    if message.text == cf.get_text(lang, role, "buttons", "back"):
        type_info = get_type_info(lang, type_services)
        reply_markup, _ = await kb.services_button(lang, type_id=type.get("id"))
        await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        await message.answer(type_info, parse_mode="HTML")
        await message.answer(text=cf.get_text(lang, role,'message_text', 'optionforservices'), reply_markup=reply_markup)
        await state.set_state(st.user.date)
    
    elif message.text == cf.get_text(lang, role, "buttons", "today"):
        dates = datetime.now(cf.tashkent).date()
        service["date"] = dates
        reply_markup, _ = await kb.show_time_slots(lang, dates, barber.get("id"), service['id'])
        await state.update_data(service=service)
        await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        await message.answer(text=cf.get_text(lang, role,'message_text', 'select_time'),
                             reply_markup=reply_markup)
        await state.set_state(st.user.check_selected_time)

    elif message.text == cf.get_text(lang, role,"buttons", "another_day"):
        reply_markup, _ = await kb.another_day(lang)
        await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        await message.answer(text=cf.get_text(lang, role,'message_text', 'another_day'),
                                reply_markup=reply_markup)
        await state.update_data(last_state="another_day")
        await state.set_state(st.user.check_selected_date)

    else:
        await message.answer(text=cf.get_text(lang, "errors", "unknown_command"))


@router.message(st.user.check_selected_time)
async def check_selected_time(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    barber = data.get("barber")
    service = data.get("service")
    lang = data.get("lang")

    _, time_slot = await kb.show_time_slots(lang, service.get("date"), barber.get("id"), service.get("id"))

    if message.text == cf.get_text(lang, role, "buttons", "back"):
        if data["last_state"] == "another_day":
            reply_markup, _ = await kb.another_day(lang)
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            await message.answer(text=cf.get_text(lang, role, 'message_text', 'another_day'),
                                 reply_markup=reply_markup)
            await state.set_state(st.user.check_selected_date)

        else:
            service_info = get_service_info(lang, service)
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            await message.answer(service_info, parse_mode="HTML")
            await message.answer(text=cf.get_text(lang, role,'message_text', 'select_date'), reply_markup=await kb.date(lang))
            await state.set_state(st.user.time)

    elif message.text in time_slot:
        service["time"] = message.text
        await state.update_data(service=service)
        booking_msg = (
            f"🕒 Vaqt/Время: <b>{message.text}</b>\n"
            f"✂️ Xizmat/Услуга: <b>{service['name']}</b>\n"
            f"💰 Narx/Цена: <b>{service['price']}</b>\n"
            f"💇‍♂️ Barber/Барбер: <b>{barber['first_name']}</b>\n"
            f"📅 Kun/День: <b>{service['date']}</b>"
        )
        await message.answer(text=f"{booking_msg}\n\n{cf.get_text(lang, role,'message_text', 'confirm_booking')}", parse_mode="HTML",reply_markup=kb.confirm_reject(lang))
        await state.set_state(st.user.confirm_booking)

    else:
        await message.answer(text=cf.get_text(lang, "errors", "unknown_command"))


@router.message(st.user.check_selected_date)
async def check_selected_date(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    barber = data.get("barber")
    service = data.get("service")
    lang = data.get("lang")

    _, another_day_btn = await kb.another_day(lang)

    if message.text == cf.get_text(lang, role, "buttons", "back"):
        service_info = get_service_info(lang, service)
        await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        await message.answer(service_info, parse_mode="HTML")
        await message.answer(text=cf.get_text(lang, role,'message_text', 'select_date'), reply_markup=await kb.date(lang))
        await state.set_state(st.user.time)

    elif message.text in another_day_btn:
        text_spl = message.text.split(" ")
        dates = text_spl[0].split("-")
        new_date = dates[2] + "-" + dates[1] + "-" + dates[0]
        service["date"] = new_date
        reply_markup, _ = await kb.show_time_slots(lang, new_date, barber.get("id"), service['id'])
        await state.update_data(service=service)
        await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        await message.answer(text=cf.get_text(lang, role,'message_text', 'select_time'),
                             reply_markup=reply_markup)
        await state.set_state(st.user.check_selected_time)

    else:
        await message.answer(text=cf.get_text(lang, "errors", "unknown_command"))


@router.message(st.user.confirm_booking)
async def confirm_booking(message: Message, state: FSMContext):

    def to_utc_iso_z(dt: datetime) -> str:
        return dt.isoformat(timespec="seconds") + "Z"

    user_id = message.from_user.id
    data = await state.get_data()
    my_infos = data.get("my_infos")
    barber = data.get("barber")
    lang = data.get('lang')
    service = data.get("service")

    if message.text == cf.get_text(lang, "director","button", "confirm"):
        date_obj = service["date"]
        if isinstance(date_obj, dt.date):
            date_str = date_obj.strftime("%Y-%m-%d")
        else:
            date_str = str(date_obj)

        start_dt = dt.datetime.combine(
            dt.datetime.strptime(date_str, "%Y-%m-%d").date(),
            dt.datetime.strptime(service["time"], "%H:%M").time()
        )
        datas = { "user": my_infos["id"], "barber": barber.get("id"), "service": service["id"], "start_time": to_utc_iso_z(start_dt) }
        booking = await db.create_booking(datas)
        send_at = next_day_utc_15(booking["end_time"])
        await add_pending(booking_id=booking["id"], user_id=my_infos.get("id"), telegram_id=my_infos.get("telegram_id"), barber_id=barber.get("id"), send_at_iso_utc=send_at, lang=lang)

        if booking:
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            await message.answer(text=cf.get_text(lang, role, 'message_text', 'booking_successful'), reply_markup=kb.us_main_menu(lang, roles=my_infos.get("roles")))
            await state.set_state(st.user.main_menu)

    elif message.text == cf.get_text(lang, "director","button", "back"):
        reply_markup, _ = await kb.show_time_slots(lang, service.get("date"), barber.get("id"), service['id'])
        await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        await message.answer(text=cf.get_text(lang, role,'message_text', 'select_time'), reply_markup=reply_markup)
        await state.set_state(st.user.check_selected_time)

    elif message.text == cf.get_text(lang, "director", "button", "back_main"):
        await message.answer(text=cf.get_text(lang, role,'message_text', 'main'), reply_markup=kb.us_main_menu(lang, roles=my_infos.get("roles")))
        await state.set_state(st.user.main_menu)

    else:
        await message.answer(text=cf.get_text(lang, "errors", "unknown_command"))