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

##################################################################################################################

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
    for btn in buttons:
        kb.row(KeyboardButton(text=cf.get_text(lang, role, "button", btn)))
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])


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

##################################################################################################################

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

##################################################################################################################

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

##################################################################################################################

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

##################################################################################################################

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

##################################################################################################################

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