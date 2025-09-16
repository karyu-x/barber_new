from datetime import datetime, timedelta

from aiogram.types import KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from configs import functions as cf
from databases import database as db

role = "director"

def back(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])


def back_main(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back"))
    )
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])


def confirm_reject(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "confirm")))
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

def location_back(lang):
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text=cf.get_text(lang, role, "button", "location"), request_location=True))
    kb.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

##################################################################################################################

def us_main_menu(lang: str, roles: list[int] | None = None):
    roles = roles or []
    role_keys = {cf.ROLE_ID_TO_KEY[r] for r in roles if r in cf.ROLE_ID_TO_KEY}

    kb = ReplyKeyboardBuilder()

    if not role_keys or "client" in role_keys:
        rk = "client"
        kb.row(
            KeyboardButton(text=cf.get_text(lang, rk, "buttons", "booking")),
            KeyboardButton(text=cf.get_text(lang, rk, "buttons", "booking_history")),
        )
        kb.row(
            KeyboardButton(text=cf.get_text(lang, rk, "buttons", "contact_menu")),
            KeyboardButton(text=cf.get_text(lang, rk, "buttons", "location")),
        )
        kb.row(
            KeyboardButton(text=cf.get_text(lang, rk, "buttons", "price_list")),
            KeyboardButton(text=cf.get_text(lang, rk, "buttons", "change_lang")),
        )

    ordered = ["barber", "admin", "director"]
    role_switch_buttons = []
    for rk in ordered:
        if rk == "admin" and "director" in role_keys:
            continue
        if rk in role_keys:
            role_switch_buttons.append(KeyboardButton(text=cf.get_role_menu_label(rk)))

    if role_switch_buttons:
        kb.row(*role_switch_buttons)

    kb.adjust(2)
    placeholder = getattr(cf, "translations", {}).get("input_field_msg", "")
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=placeholder)


def br_main_menu(lang):
    kb = ReplyKeyboardBuilder()
    role = "barber"
    kb.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "bookings")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "breaks")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "cabinet")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "types")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "user_menu")),
        width=2
    )
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

def ad_main_menu(lang, telegram_id):
    kb = ReplyKeyboardBuilder()
    buttons = cf.get_admin_buttons(telegram_id)
    if buttons:
        for btn in buttons:
            kb.row(KeyboardButton(text=cf.get_text(lang, role, "button", btn)))
        kb.adjust(2)
        return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])
    else:
        return None


def dr_main_menu(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "bookings")), 
        KeyboardButton(text=cf.get_text(lang, role, "button", "notifications")), 
        KeyboardButton(text=cf.get_text(lang, role, "button", "clients")), 
        KeyboardButton(text=cf.get_text(lang, role, "button", "settings")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "analytics")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "user_menu")),
        width=2
    )
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

##################################################### NOTIFICATION  #############################################################

def notifications(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(
        KeyboardButton(text=cf.get_text(lang, role, "button", "input_text")), KeyboardButton(text=cf.get_text(lang, role, "button", "input_photo")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "input_button")), KeyboardButton(text=cf.get_text(lang, role, "button", "check_post"))
    )
    keyboard.adjust(2)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

def check_post(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(
        KeyboardButton(text=cf.get_text(lang, role, "button", "preview_post")), KeyboardButton(text=cf.get_text(lang, role, "button", "confirm_post")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back"))
    )
    keyboard.adjust(2)
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

###################################################### BOOKINGS ############################################################

def br_bookings(lang):
    kb = ReplyKeyboardBuilder()
    role = "barber"
    kb.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "bookings_today")), KeyboardButton(text=cf.get_text(lang, role, "button", "bookings_otherday")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "back")),
        width=2
    )
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])


def br_bookings_today(lang, bookings):
    kb = ReplyKeyboardBuilder()
    role = "barber"
    for booking in bookings:
        kb.add(KeyboardButton(text=booking))
    kb.adjust(3)
    kb.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])


def br_bookings_otherday(lang):
    kb = ReplyKeyboardBuilder()
    role = "barber"
    days = cf.get_days_from_today(lang)
    for day in days:
        kb.add(KeyboardButton(text=day["date"]))
    kb.adjust(3)
    kb.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])


def bookings(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(
        KeyboardButton(text=cf.get_text(lang, role, "button", "bookings_today")), KeyboardButton(text=cf.get_text(lang, role, "button", "bookings_otherday")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "bookings_cancel")), KeyboardButton(text=cf.get_text(lang, role, "button", "bookings_forward"))
    )
    keyboard.adjust(2)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

async def bookings_today(lang):
    keyboard = ReplyKeyboardBuilder()
    barbers = await db.get_barbers_all()
    for barber in barbers:
        keyboard.add(KeyboardButton(text=barber["first_name"]))
    keyboard.adjust(2)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

async def bookings_otherday(lang):
    keyboard = ReplyKeyboardBuilder()
    other_days = cf.get_days_from_today(lang)
    for day in other_days:
        keyboard.add(KeyboardButton(text=day["date"]))
    keyboard.adjust(3)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

######################################################## BREAKS ##########################################################

def br_breaks(lang):
    kb = ReplyKeyboardBuilder()
    role = "barber"
    kb.add(
        KeyboardButton(text=cf.get_text(lang, role, "button", "breaks_all")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "break_add")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "break_edit")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "break_delete")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "back"))
    )
    kb.adjust(1, 2, 1)
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])


async def break_buttons(lang, barber_id):
    kb = ReplyKeyboardBuilder()
    role = "barber"
    breaks = db.get_barber_breaks(barber_id)
    for brk in breaks:
        kb.add(
            KeyboardButton(text=f"{brk['id']} {brk['start_time'].split('T')[1][:5]} - {brk['end_time'].split('T')[1][:5]}")
        )
    kb.adjust(2)
    kb.add(KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

####################################################  SERVICES & TYPES ##############################################################

async def br_types(lang, barber_id):
    kb = ReplyKeyboardBuilder()
    role = "barber"
    barber_types = await db.get_barber_types(barber_id)
    for b_type in barber_types:
        kb.add(KeyboardButton(text=f'🆔 {b_type["id"]} - 💈 {b_type["name"]}'))
    kb.adjust(2)
    kb.row(KeyboardButton(text=cf.get_text(lang, role, "button", "type_add")), KeyboardButton(text=cf.get_text(lang, role, "button", "type_delete")),
           KeyboardButton(text=cf.get_text(lang, role, "button", "back")), width=2)
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])


async def br_services(lang, type_id):
    kb = ReplyKeyboardBuilder()
    role = "barber"
    barber_services = await db.get_barber_services(type_id)
    for b_service in barber_services:
        kb.add(KeyboardButton(text=f'🆔 {b_service["id"]} - ✂️ {b_service["name"]}'))
    kb.adjust(3)
    kb.row(KeyboardButton(text=cf.get_text(lang, role, "button", "service_add")), KeyboardButton(text=cf.get_text(lang, role, "button", "service_delete")),
           KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")),
            width=2)
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])


def br_service_detail(lang):
    kb = ReplyKeyboardBuilder()
    role = "barber"
    kb.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "name_edit")), KeyboardButton(text=cf.get_text(lang, role, "button", "description_edit")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "duration_edit")), KeyboardButton(text=cf.get_text(lang, role, "button", "price_edit")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")),
        width=2)
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

######################################################## CABINET ##########################################################

def br_cabinet(lang):
    kb = ReplyKeyboardBuilder()
    role = "barber"
    kb.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "phone_edit")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "about_edit")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "photo_edit")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "time_edit")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "back")), 
        KeyboardButton(text=cf.get_text(lang, role, "button", "language_edit")), width=2
    )
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

def br_cabinet_language(lang):
    kb = ReplyKeyboardBuilder()
    role = "barber"
    kb.row(
        KeyboardButton(text="🇺🇿 uz"), KeyboardButton(text="🇷🇺 ru"),
        KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")),
        width=2
    )
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])


######################################################## ANALYTIC ##########################################################

def analytics(lang):
    kb = ReplyKeyboardBuilder()
    kb.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "weekly_clients")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "barber_activities")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "barber_ratings")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "top_services")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "back")),
        width=2
    )
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

###################################################  USER  #############################################################

def start_key():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="🇺🇿 uz"), KeyboardButton(text="🇷🇺 ru"))
    keyboard.adjust(3)
    return keyboard.as_markup(resize_keyboard=True)


def ask_phone(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text=cf.get_text(lang, "client", "buttons", "contact"), request_contact=True))
    keyboard.adjust(1)
    return keyboard.as_markup(resize_keyboard=True)


def conf(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text=cf.get_text(lang, "client", "buttons", "confirm")), KeyboardButton(text=cf.get_text(lang, "client", "buttons", "rejected")))
    keyboard.adjust(2)
    return keyboard.as_markup(resize_keyboard=True)


def back(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text=cf.get_text(lang, "client", "buttons", "back")))
    keyboard.adjust(1)
    return keyboard.as_markup(resize_keyboard=True)


def language(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="🇺🇿 uz"), KeyboardButton(text="🇷🇺 ru"),
                 KeyboardButton(text=cf.get_text(lang, "client", "buttons", "back")))
    keyboard.adjust(2, 1)
    return keyboard.as_markup(resize_keyboard=True)


async def barber_name(lang):
    barber_with_tg_id = {}
    keyboard = ReplyKeyboardBuilder()
    names = await db.get_barbers_all()
    for i in names:
        barber_with_tg_id[i["first_name"]] = i["telegram_id"]
        keyboard.add(KeyboardButton(text=i["first_name"]))
    keyboard.add(KeyboardButton(text=cf.get_text(lang, "client", "buttons", "back")))
    keyboard.adjust(2, 1)
    return keyboard.as_markup(resize_keyboard=True), barber_with_tg_id


async def booking_history(lang, tg_id):
    keyboard = ReplyKeyboardBuilder()
    booking_hist = await db.user_booking_history(tg_id)
    for i in booking_hist:
        day = i['start_time'].split("T")[0]
        time = i["start_time"].split("T")[1][:5]
        keyboard.add(KeyboardButton(text=f"{day} {time}"))
    keyboard.add(KeyboardButton(text=cf.get_text(lang, "client", "buttons", "back")))
    keyboard.adjust(2)
    return keyboard.as_markup(resize_keyboard=True)


async def types_button(lang, tg_id):
    type_with_id = {}
    keyboard = ReplyKeyboardBuilder()
    service_type_barber = await db.get_barber_types_and_services(tg_id)
    for i in service_type_barber:
        keyboard.add(KeyboardButton(text=i["name"]))
        type_with_id[i["name"]] = i["id"]
    keyboard.add(KeyboardButton(text=cf.get_text(lang, "client", "buttons", "back")))
    keyboard.adjust(2, 1)
    return keyboard.as_markup(resize_keyboard=True), type_with_id


async def services_button(lang, type_id):
    service_with_id = {}
    keyboard = ReplyKeyboardBuilder()
    services = await db.get_barber_services(type_id)
    for i in services:
        keyboard.add(KeyboardButton(text=i["name"].strip()))
        service_with_id[i["name"]] = i["id"]
    keyboard.add(KeyboardButton(text=cf.get_text(lang, "client", "buttons", "back")))
    keyboard.adjust(2, 1)
    return keyboard.as_markup(resize_keyboard=True), service_with_id


async def date(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text=cf.get_text(lang, "client", "buttons", "today")),
                 KeyboardButton(text=cf.get_text(lang, "client", "buttons", "another_day")))
    keyboard.add(KeyboardButton(text=cf.get_text(lang, "client", "buttons", "back")))
    keyboard.adjust(2, 1)
    return keyboard.as_markup(resize_keyboard=True)


async def show_time_slots(lang, dates, barber_id, service_id):
    available_slots = []
    keyboard = ReplyKeyboardBuilder()
    time_slots = await db.get_time_api(dates, barber_id, service_id)
    time_now = datetime.now(cf.tashkent).time()
    day = datetime.now(cf.tashkent).strftime("%Y-%m-%d")

    if time_slots:
        for i in time_slots.get("available_slots", []):
            try:
                slot_time = datetime.strptime(i, "%H:%M").time()
            except ValueError:
                continue

            if str(dates) == day:
                if time_now < slot_time:
                    keyboard.add(KeyboardButton(text=i))
                    available_slots.append(i)
            else:
                keyboard.add(KeyboardButton(text=i))
                available_slots.append(i)

    keyboard.add(KeyboardButton(text=cf.get_text(lang, "client", "buttons", "back")))
    keyboard.adjust(3)
    return keyboard.as_markup(resize_keyboard=True), available_slots


def get_30_day_range_from_today(lang: str) -> list[str]:
    today = datetime.now(cf.tashkent)
    start_date = today + timedelta(days=1)
    weekdays = {
        "🇺🇿 uz": ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"],
        "🇷🇺 ru": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],
    }
    names = weekdays.get(lang, weekdays["🇺🇿 uz"])
    date_list = [
        (start_date + timedelta(days=i)).strftime(f"%d-%m-%Y ({names[(start_date + timedelta(days=i)).weekday()]})")
        for i in range(30)
    ]
    print(date_list)
    return date_list


async def another_day(lang):
    another_day_btn = []
    keyboard = ReplyKeyboardBuilder()
    dates = get_30_day_range_from_today(lang)
    for i in dates:
        another_day_btn.append(i)
        keyboard.add(KeyboardButton(text=i))
    keyboard.add(KeyboardButton(text=cf.get_text(lang, "client", "buttons", "back")))
    keyboard.adjust(2)
    return keyboard.as_markup(resize_keyboard=True), another_day_btn
