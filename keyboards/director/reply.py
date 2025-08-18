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
        keyboard.add(KeyboardButton(text=day))
    keyboard.adjust(3)
    keyboard.row(KeyboardButton(text=cf.get_text(lang, role, "button", "back_main")), KeyboardButton(text=cf.get_text(lang, role, "button", "back")))
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
