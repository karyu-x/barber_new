from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from configs import buttons_config as but_cf
from configs import functions as cf
from databases.director import database as db

role = "director"

def confirm_reject(lang):
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "confirm"), callback_data="confirm"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="back"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back_main"), callback_data="main"),
        width=2
    )
    return kb.as_markup()

def post_button(buttons: list):
    kb = InlineKeyboardBuilder()
    for i in buttons:
        kb.add(InlineKeyboardButton(text=i['text'], url=i['url']))
    kb.adjust(1)
    return kb.as_markup()

################################################################################

def settings(lang: str):
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "services_prices"), callback_data="setting_btn:services_prices"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "barbers"), callback_data="setting_btn:barbers"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "admins"), callback_data="setting_btn:admins"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "working_hours"), callback_data="setting_btn:working_hours"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "language"), callback_data="setting_btn:language"),
    )
    kb.adjust(1, 2)
    kb.row(InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="setting_btn:back"))
    return kb.as_markup()

async def services_prices(lang):
    kb = InlineKeyboardBuilder()
    barbers = await db.get_barbers_all()
    for barber in barbers:
        kb.add(InlineKeyboardButton(text=barber["first_name"], callback_data=f"services_btn:{barber['telegram_id']}"))
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back_main"), callback_data="services_btn:main"),
            InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="services_btn:back"))
    return kb.as_markup()

async def barber_types(lang, barber_id):
    kb = InlineKeyboardBuilder()
    types = await db.get_barber_types(barber_id)
    kb.row(InlineKeyboardButton(text=cf.get_text(lang, role, "button", "type_add"), callback_data="types_btn:add"))
    for item in types:
        kb.add(InlineKeyboardButton(text=item["name"], callback_data=f"types_btn:{item['id']}"))
    kb.adjust(1, 2)
    kb.row(InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back_main"), callback_data="types_btn:main"), 
           InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="types_btn:back"))
    return kb.as_markup()

async def barber_services(lang, type_id):
    kb = InlineKeyboardBuilder()
    services = await db.get_barber_services(type_id)
    kb.row(InlineKeyboardButton(text=cf.get_text(lang, role, "button", "type_delete"), callback_data="service_btn:delete"))
    for item in services:
        kb.add(InlineKeyboardButton(text=item["name"], callback_data=f"service_btn:{item['id']}"))
    kb.adjust(1, 2)
    kb.row(InlineKeyboardButton(text=cf.get_text(lang, role, "button", "service_add"), callback_data="service_btn:add"))
    kb.row(InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back_main"), callback_data="service_btn:main"), 
           InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="service_btn:back"))
    return kb.as_markup()

def service_detail(lang):
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "service_delete"), callback_data="ser_detail_btn:delete"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "service_edit_name"), callback_data="ser_detail_btn:name"), 
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "service_edit_description"), callback_data="ser_detail_btn:description"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "service_edit_duration"), callback_data="ser_detail_btn:duration"), 
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "service_edit_price"), callback_data="ser_detail_btn:price"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back_main"), callback_data="ser_detail_btn:main"), 
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="ser_detail_btn:back")
    )
    kb.adjust(1, 2)
    return kb.as_markup()

async def barbers(lang):
    kb = InlineKeyboardBuilder()
    barbers = await db.get_barbers_all()
    kb.row(InlineKeyboardButton(text=cf.get_text(lang, role, "button", "barber_add"), callback_data="barber_btn:add"))
    if barbers:
        for barber in barbers:
            kb.add(InlineKeyboardButton(text=barber["first_name"], callback_data=f"barber_btn:{barber['telegram_id']}"))
    kb.adjust(1, 2)
    kb.row(
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back_main"), callback_data="barber_btn:main"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="barber_btn:back")
    )
    return kb.as_markup()

def barber_detail(lang):
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "barber_delete"), callback_data="bar_detail_btn:delete"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "barber_edit_phone"), callback_data="bar_detail_btn:phone"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "barber_edit_description"), callback_data="bar_detail_btn:description"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "barber_edit_photo"), callback_data="bar_detail_btn:photo"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "barber_edit_time"), callback_data="bar_detail_btn:time"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back_main"), callback_data="bar_detail_btn:main"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="bar_detail_btn:back")
    )
    kb.adjust(1, 2)
    return kb.as_markup()

async def admins(lang):
    kb = InlineKeyboardBuilder()
    admins = await db.get_admins_all()
    kb.row(InlineKeyboardButton(text=cf.get_text(lang, role, "button", "admin_add"), callback_data="admin_btn:add"))
    if admins:
        for admin in admins:
            kb.add(InlineKeyboardButton(text=admin["first_name"], callback_data=f"admin_btn:{admin['telegram_id']}"))
    kb.adjust(1, 2)
    kb.row(
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back_main"), callback_data="admin_btn:main"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="admin_btn:back")
    )
    return kb.as_markup()

def admin_detail(lang):
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "admin_delete"), callback_data="adm_detail_btn:delete"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "admin_edit_phone"), callback_data="adm_detail_btn:phone"), 
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "admin_edit_button"), callback_data="adm_detail_btn:button"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back_main"), callback_data="adm_detail_btn:main"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="adm_detail_btn:back")
    )
    kb.adjust(1, 2)
    return kb.as_markup()

def build_admin_buttons_editor(lang: str, selected: set[str]):
    kb = InlineKeyboardBuilder()
    for bid in but_cf.AVAILABLE_BUTTONS:
        title = but_cf.button_title(lang, role, bid)
        mark = "✅" if bid in selected else "⬜️"
        kb.add(InlineKeyboardButton(
            text=f"{mark} {title}",
            callback_data=f"adm_btn:toggle:{bid}"
        ))
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text=cf.get_text(lang, role, "button", "confirm"), callback_data="adm_btn:save"),
            InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="adm_btn:back"))
    return kb.as_markup()

def language(lang):
    kb = InlineKeyboardBuilder()
    kb.add( 
        InlineKeyboardButton(text="🇺🇿 uz", callback_data="language_btn:uz"), 
        InlineKeyboardButton(text="🇷🇺 ru", callback_data="language_btn:ru"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back_main"), callback_data="language_btn:main"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="language_btn:back")
    )
    kb.adjust(2)
    return kb.as_markup()

def working_hours(lang):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back_main"), callback_data="hours:main"),
            InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="hours:back"))
    return kb.as_markup()