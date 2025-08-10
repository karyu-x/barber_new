from aiogram.types import KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import configs.functions as cf
import databases.director.database as db

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
    keyboard.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "confirm")), KeyboardButton(text=cf.get_text(lang, role, "button", "reject")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")),
        width=2
    )
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

##################################################################################################################

def main_menu(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "bookings")), KeyboardButton(text=cf.get_text(lang, role, "button", "notifications")), 
        KeyboardButton(text=cf.get_text(lang, role, "button", "clients")), KeyboardButton(text=cf.get_text(lang, role, "button", "settings")),
        width=2
    )
    keyboard.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "analytics")), 
        KeyboardButton(text=cf.get_text(lang, role, "button", "finance")), 
        KeyboardButton(text=cf.get_text(lang, role, "button", "journal"))
    )
    keyboard.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "feedback")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "user_menu"))
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

def bookings(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(
        KeyboardButton(text=cf.get_text(lang, role, "button", "today_books")), KeyboardButton(text=cf.get_text(lang, role, "button", "other_day_books")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "cancel_books")), KeyboardButton(text=cf.get_text(lang, role, "button", "reschedule_books"))
    )
    keyboard.adjust(2)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

async def today_books(lang):
    keyboard = ReplyKeyboardBuilder()
    barbers = await db.get_barbers_all()
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "all_today_bookings")))
    for barber in barbers:
        keyboard.add(KeyboardButton(text=barber["first_name"]))
    keyboard.adjust(1, 2)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

def other_day_books(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add()
    keyboard.adjust()
    keyboard.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back"))
    )
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

def cancel_books(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add()
    keyboard.adjust()
    keyboard.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back"))
    )
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

def reschedule_books(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add()
    keyboard.adjust()
    keyboard.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back"))
    )
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

##################################################################################################################

def settings(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(
        KeyboardButton(text=cf.get_text(lang, role, "button", "services_prices")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "barbers")), KeyboardButton(text=cf.get_text(lang, role, "button", "admins")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "working_hours")), KeyboardButton(text=cf.get_text(lang, role, "button", "language"))
    )
    keyboard.adjust(1, 2)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

#### SERVICE MENU
async def services_prices(lang):
    keyboard = ReplyKeyboardBuilder()
    barbers = await db.get_barbers_all()
    for item in barbers:
        keyboard.add(KeyboardButton(text=item["first_name"]))
    keyboard.adjust(2)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

#### BARBER TYPES MENU
async def barber_types(lang, barber_id):
    keyboard = ReplyKeyboardBuilder()
    types = await db.get_barber_types(barber_id)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "add_service_type")))
    for item in types:
        if barber_id == item["barber"]:
            keyboard.add(KeyboardButton(text=item["name"]))
    keyboard.adjust(1, 2)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

#### BARBER SERVICES MENU
async def barber_services(lang, type_id):
    keyboard = ReplyKeyboardBuilder()
    services = await db.get_barber_services(type_id)
    keyboard.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "delete_service_type")),
    )
    for item in services:
            keyboard.add(KeyboardButton(text=item["name"]))
    keyboard.adjust(1, 2)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "add_service")))
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

#### SERVICE DETAIL MENU
def service_detail(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(
        KeyboardButton(text=cf.get_text(lang, role, "button", "delete_service")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "edit_service_name")), KeyboardButton(text=cf.get_text(lang, role, "button", "edit_service_description")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "edit_service_duration")), KeyboardButton(text=cf.get_text(lang, role, "button", "edit_service_price")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back"))
    )
    keyboard.adjust(1, 2)
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

#### EDIT SERVICE MENU
def edit_service(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.row(
        
        KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")),
        width=2
    )
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

#### BARBERS MENU
async def barbers(lang):
    keyboard = ReplyKeyboardBuilder()
    barbers = await db.get_barbers_all()
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "add_barber")))
    for item in barbers:
        keyboard.add(KeyboardButton(text=item["first_name"]))
    keyboard.adjust(1, 2)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

#### BARBER DETAIL MENU
def barber_detail(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(
        KeyboardButton(text=cf.get_text(lang, role, "button", "delete_barber")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "edit_barber_phone")), KeyboardButton(text=cf.get_text(lang, role, "button", "edit_barber_description")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "edit_barber_photo")), KeyboardButton(text=cf.get_text(lang, role, "button", "edit_barber_time"))
    )
    keyboard.adjust(1, 2)
    keyboard.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back"))
    )
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

async def admins(lang):
    keyboard = ReplyKeyboardBuilder()

    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

#### WORKING HOURS MENU
def working_hours(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add()
    keyboard.row(
        KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back"))
    )
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

#### LANGUAGE MENU
def language(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.row(
        KeyboardButton(text="🇺🇿 uz"), KeyboardButton(text="🇷🇺 ru"),
        KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")), width=2
    )
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

##################################################################################################################

def clients(lang):
    keyboard = ReplyKeyboardBuilder()

    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

##################################################################################################################

def analytics(lang):
    keyboard = ReplyKeyboardBuilder()

    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

##################################################################################################################

def finance(lang):
    keyboard = ReplyKeyboardBuilder()

    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

##################################################################################################################

def journal(lang):
    keyboard = ReplyKeyboardBuilder()

    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

##################################################################################################################

def feedback(lang):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(
        KeyboardButton(text=cf.get_text(lang, role, "button", "feedback_rating")), 
        KeyboardButton(text=cf.get_text(lang, role, "button", "feedback_reviews")),
        KeyboardButton(text=cf.get_text(lang, role, "button", "feedback_complaints")), 
        KeyboardButton(text=cf.get_text(lang, role, "button", "feedback_pinned"))
    )
    keyboard.adjust(2)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
    return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

# def feedback_type(lang):
#     keyboard = ReplyKeyboardBuilder()
#     keyboard.row(
#         KeyboardButton(text=cf.get_text(lang, role, "button", "feedback_barbers")), KeyboardButton(text=cf.get_text(lang, role, "button", "feedback_company")),
#         KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")),
#         width=2
#     )
#     return keyboard.as_markup(resize_keyboard=True, input_field_placeholder=cf.translations["input_field_msg"])

##################################################################################################################
