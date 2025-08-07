from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def post_button(buttons):
    inline_keyboard = InlineKeyboardBuilder()
    for i in buttons:
        inline_keyboard.add(InlineKeyboardButton(text=i['text'], url=i['url']))
    inline_keyboard.adjust(1)
    return inline_keyboard.as_markup()