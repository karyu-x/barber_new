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
user_lang = {"uz":"🇺🇿 uz", "ru":"🇷🇺 ru"}

role = "client"

def next_day_utc_15(end_time_utc_iso: str) -> str:
    end_dt = datetime.fromisoformat(end_time_utc_iso.replace("Z", "+00:00"))
    target = datetime.combine((end_dt.date() + timedelta(days=1)), dtime(15, 0), tzinfo=timezone.utc)
    return target.isoformat(timespec="seconds").replace("+00:00", "Z")
    # end_dt = datetime.fromisoformat(end_time_utc_iso.replace("Z", "+00:00"))
    # target = end_dt + timedelta(minutes=5)
    # target = target.astimezone(timezone.utc)
    # return target.isoformat(timespec="seconds").replace("+00:00", "Z")


@router.message(st.user.language)
async def ask_phone(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text in {"🇺🇿 uz":"🇺🇿 uz", "🇷🇺 ru":"🇷🇺 ru",}:
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
            await message.answer(text=cf.get_text(lang, role,'message_text', 'barber_name'), reply_markup=await kb.barber_name(lang))
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
                if kb.ad_main_menu(lang, user_id) != "no buttons":
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
    try:
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

    except Exception as e:
        print(f"Error: {e}")


@router.message(st.user.booking_history)
async def booking_history(message: Message, state: FSMContext):
    try:
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
                    await message.answer(text=booking_msg, parse_mode="HTML")

    except Exception as e:
        print(f"Error:{e}")



# ////////////////// barber_name \\\\\\\\\\\\\\\\\\\\\\\
from keyboards.reply import barber_with_telegramid, selected_service, check_selected_types, time_slot, another_day_btn
@router.message(st.user.barber_name)
async def barber_name(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        data = await state.get_data()
        my_infos = data.get("my_infos")
        lang = data['lang']
        if message.text == cf.get_text(lang, role,"buttons", "back"):
            await message.answer(text=cf.get_text(lang, role,'message_text', 'menu'), reply_markup=kb.us_main_menu(lang, my_infos.get("roles")))
            await state.set_state(st.user.main_menu)
        elif message.text in barber_with_telegramid:
            await state.update_data(barber_name=message.text)
            barber_tg_id = barber_with_telegramid[message.text]
            await state.update_data(service={"barber_name": message.text})
            await message.answer(text=cf.get_text(lang, role,'message_text', 'service_type'), reply_markup= await kb.services(lang,barber_tg_id))
            await state.set_state(st.user.check_service_type)
    except Exception as e:
        print(f"Error:{e}")



# ////////////////// check_service_type \\\\\\\\\\\\\\\\\\\\\\\
@router.message(st.user.check_service_type)
async def check_service_type(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        data = await state.get_data()
        lang = data['lang']
        if message.text == cf.get_text(lang, role,"buttons", "back"):
            selected_service.clear()
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            await message.answer(text=cf.get_text(lang, role,'message_text', 'barber_name'),reply_markup=await kb.barber_name(lang))
            await state.set_state(st.user.barber_name)
        elif message.text in selected_service:
            barber_id = selected_service[message.text]
            await state.update_data(barber_id=selected_service["barber_id"])
            await state.update_data(selected_service=message.text)
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            await message.answer(text=cf.get_text(lang, role,'message_text', 'optionforservices'), reply_markup=await kb.type_of_selected_service(lang, barber_id))
            await state.set_state(st.user.date)

    except Exception as e:
        print(f"Error:{e}")


@router.message(st.user.date)
async def date(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        data = await state.get_data()
        lang = data['lang']
        if message.text == cf.get_text(lang, role,"buttons", "back"):
            check_selected_types.clear()
            barber_tg_id = barber_with_telegramid[data['barber_name']]
            await message.answer(text=cf.get_text(lang, role,'message_text', 'service_type'),
                                 reply_markup=await kb.services(lang, barber_tg_id))
            await state.set_state(st.user.check_service_type)

        if message.text in check_selected_types:
            service = data["service"]
            service["name"] = message.text
            service["service_id"] = selected_service["service_id"]
            await state.update_data(service=service)
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            await message.answer(text=cf.get_text(lang, role,'message_text', 'select_date'),reply_markup=await kb.date(lang))
            await state.set_state(st.user.time)

    except Exception as e:
        print(f"Error:{e}")





@router.message(st.user.time)
async def time(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        data = await state.get_data()
        lang = data['lang']

        if message.text == cf.get_text(lang, role,"buttons", "back"):
            barber_id = selected_service[data['selected_service']]
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            await message.answer(text=cf.get_text(lang, role,'message_text', 'optionforservices'),
                                 reply_markup=await kb.type_of_selected_service(lang, barber_id))
            await state.set_state(st.user.date)

        if message.text == cf.get_text(lang, role,"buttons", "today"):
            dates = datetime.today().date()
            service = data["service"]
            service["date"] = dates
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            await message.answer(text=cf.get_text(lang, role,'message_text', 'select_time'),
                                 reply_markup=await kb.show_time_slots(lang, dates, data['barber_id'], service['service_id']))
            await state.update_data(service=service)
            await state.set_state(st.user.check_selected_time)


        #  Boshqa kuni buttonlarini boshqarish
        if message.text == cf.get_text(lang, role,"buttons", "another_day"):
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            await message.answer(text=cf.get_text(lang, role,'message_text', 'another_day'),
                                 reply_markup=await kb.another_day(lang))
            await state.set_state(st.user.check_selected_date)

    except Exception as e:
        print(f"Error:{e}")



@router.message(st.user.check_selected_time)
async def check_selected_time(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        data = await state.get_data()
        service = data["service"]
        lang = data['lang']
        if message.text == cf.get_text(lang, role,"buttons", "back"):
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            await state.update_data(service_id=selected_service["service_id"])
            await message.answer(text=cf.get_text(lang, role,'message_text', 'select_date'), reply_markup=await kb.date(lang))
            await state.set_state(st.user.time)
            time_slot.clear()
        elif message.text in time_slot:
            service["time"] = message.text
            service_price = await db.get_barber_service_by_id(service_id=service["service_id"])
            await state.update_data(service=service)
            booking_msg = (
                f"🕒 Vaqt/Время: <b>{message.text}</b>\n"
                f"✂️ Xizmat/Услуга: <b>{service['name']}</b>\n"
                f"💰 Narx/Цена: <b>{service_price['price']}</b>\n"
                f"💇‍♂️ Barber/Барбер: <b>{service['barber_name']}</b>\n"
                f"📅 Kun/День: <b>{service['date']}</b>"
            )
            await state.update_data(booking_msg=booking_msg)
            await message.answer(text=f"{booking_msg}\n\n{cf.get_text(lang, role,'message_text', 'confirm_booking')}", parse_mode="HTML",reply_markup=kb.confirm_reject(lang))
            await state.set_state(st.user.confirm_booking)

    except Exception as e:
        print(f"Error:{e}")



@router.message(st.user.check_selected_date)
async def check_selected_date(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        data = await state.get_data()
        lang = data['lang']
        if message.text == cf.get_text(lang, role,"buttons", "back"):
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            await message.answer(text=cf.get_text(lang, role,'message_text', 'select_date'), reply_markup=await kb.date(lang))
            await state.set_state(st.user.time)

        if message.text in another_day_btn:
            service = data["service"]
            dates = message.text.split("-")
            new_date = dates[2] + "-" + dates[1] + "-" + dates[0]
            service["date"] = new_date
            await state.update_data(service=service)
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            await message.answer(text=cf.get_text(lang, role,'message_text', 'select_time'),
                                 reply_markup=await kb.show_time_slots(lang, new_date, data['barber_id'], service['service_id']))
            await state.set_state(st.user.check_selected_time)

    except Exception as e:
        print(f"Error:{e}")


@router.message(st.user.confirm_booking)
async def confirm_booking(message: Message, state: FSMContext):

    def to_utc_iso_z(dt: datetime) -> str:
        return dt.isoformat(timespec="seconds") + "Z"

    user_id = message.from_user.id
    data = await state.get_data()
    my_infos = data['my_infos']
    lang = data['lang']
    service = data['service']

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
        datas = { "user": my_infos["id"], "barber": data["barber_id"], "service": service["service_id"], "start_time": to_utc_iso_z(start_dt) }
        booking = await db.create_booking(datas)
        send_at = next_day_utc_15(booking["end_time"])
        await add_pending(booking_id=booking["id"], user_id=my_infos.get("id"), telegram_id=my_infos.get("telegram_id"), barber_id=data["barber_id"], send_at_iso_utc=send_at, lang=lang)

        if booking:
            await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            await message.answer(text=cf.get_text(lang, role, 'message_text', 'booking_successful'), reply_markup=kb.us_main_menu(lang, roles=my_infos.get("roles")))
            await state.set_state(st.user.main_menu)

    elif message.text == cf.get_text(lang, "director","button", "back"):
        await message.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        await message.answer(text=cf.get_text(lang, role,'message_text', 'select_time'), reply_markup=await kb.show_time_slots(lang, service["date"], data['barber_id'], service['service_id']))
        await state.set_state(st.user.check_selected_time)

    elif message.text == cf.get_text(lang, "director", "button", "back_main"):
        await message.answer(text=cf.get_text(lang, role,'message_text', 'main'), reply_markup=kb.us_main_menu(lang, roles=my_infos.get("roles")))
        await state.set_state(st.user.main_menu)


