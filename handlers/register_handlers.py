from aiogram import Bot, Router, Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.filters import StateFilter
from decouple import config

from configs import functions as cf

from keyboards.user import reply as kb_user
from keyboards.barber import reply as kb_barber
from keyboards.admin import reply as kb_admin
from keyboards.director import reply as kb_director

from states.user import state as st_user
from states.barber import state as st_barber
from states.admin import state as st_admin
from states.director import state as st_director

from databases.user import database as db_user
from databases.barber import database as db_barber
from databases.admin import database as db_admin
from databases.director import database as db_director

from handlers.user.handler import user_router
from handlers.barber.handler import barber_router
from handlers.admin.handler import admin_router
from handlers.director.handler import director_router

bot = Bot(config("TOKEN"))
dp = Dispatcher()
router = Router()


@router.message(F.text, StateFilter(default_state))
async def cmd_bot(message: Message, state: FSMContext):
    user_id = message.from_user.id
    old_state = await state.get_state()

    if old_state:
        return

    lang = await db_user.select_language(user_id) or "🇺🇿 uz"
    roles = [
        ("director", await db_director.get_director_by_id(user_id), st_director.director.main_menu, kb_director.main_menu),
        ("admin", db_admin.select_admin(user_id), st_admin.admin.main_menu, kb_admin.main_menu),
        ("barber", db_barber.select_barber(user_id), st_barber.barber.main_menu, kb_barber.main_menu),
        ("user", db_user.select_user(user_id), st_user.user.main_menu, kb_user.main_menu),
    ]

    for role, is_match, next_state, keyboard in roles:
        if is_match:
            caption = cf.get_text(lang, role, "message", "start_msg")
            photo = cf.get_logo_file()
            if photo:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=photo,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard(lang),
                )
            await state.update_data(lang=lang)
            await state.set_state(next_state)
            return

    photo = cf.get_logo_file()
    if photo:
        await bot.send_photo(
            chat_id=user_id,
            photo=photo,
            caption=cf.get_text(lang, "user", "message", ""),
            parse_mode="HTML",
        )
    await state.set_state(st_user.user.main_menu)


router.include_router(user_router)
router.include_router(barber_router)
router.include_router(admin_router)
router.include_router(director_router)
dp.include_router(router)