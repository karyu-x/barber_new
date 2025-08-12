from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from configs.buttons_config import AVAILABLE_BUTTONS, button_title
from configs import functions as cf

def post_button(buttons):
    inline_keyboard = InlineKeyboardBuilder()
    for i in buttons:
        inline_keyboard.add(InlineKeyboardButton(text=i['text'], url=i['url']))
    inline_keyboard.adjust(1)
    return inline_keyboard.as_markup()

def build_admin_buttons_editor(lang: str, role, selected: set[str]):
    kb = InlineKeyboardBuilder()
    for bid in AVAILABLE_BUTTONS:
        title = button_title(lang, role, bid)
        mark = "✅" if bid in selected else "⬜️"
        kb.add(InlineKeyboardButton(
            text=f"{mark} {title}",
            callback_data=f"adm_btn:toggle:{bid}"
        ))
    kb.adjust(2)
    kb.row(
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "confirm"), callback_data="adm_btn:save"),
        InlineKeyboardButton(text=cf.get_text(lang, role, "button", "back"), callback_data="adm_btn:back"),
    )
    return kb.as_markup()