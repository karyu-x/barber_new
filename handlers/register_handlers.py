# register_handlers.py
from aiogram import Bot, Router, Dispatcher, F
from aiogram.types import Message, CallbackQuery
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

from databases.director import database as db

bot = Bot(config("TOKEN"))
dp = Dispatcher()
router = Router()

ROLE_BARBER, ROLE_CLIENT, ROLE_DIRECTOR, ROLE_ADMIN = 1, 2, 3, 4
ROLE_ORDER = [ROLE_DIRECTOR, ROLE_ADMIN, ROLE_BARBER, ROLE_CLIENT]

def pick_role(roles: list[int]) -> int:
    for r in ROLE_ORDER:
        if r in (roles or []):
            return r
    return ROLE_CLIENT

@router.callback_query(F.data, StateFilter(default_state))
async def cmd_bot_cb(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    user = await db.get_user_by_telegram(uid) or {}
    roles = user.get("roles") or []
    lang = user.get("language") or "🇺🇿 uz"
    role = pick_role(roles)
    caption_key = {
        ROLE_DIRECTOR: ("director", kb_director.main_menu, st_director.director.main_menu),
        ROLE_ADMIN:    ("admin",    kb_admin.main_menu,    st_admin.admin.main_menu),
        ROLE_BARBER:   ("barber",   kb_barber.main_menu,   st_barber.barber.main_menu),
        ROLE_CLIENT:   ("user",     kb_user.main_menu,     st_user.user.main_menu),
    }[role]
    role_key, kb_builder, st = caption_key
    caption = cf.get_text(lang, role_key, "message", "start_msg")
    photo = cf.get_logo_file()

    await call.message.delete()

    if photo:
        await call.bot.send_photo(
            chat_id=uid,
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=kb_builder(lang),
        )
    else:
        await call.bot.send_message(uid, caption, reply_markup=kb_builder(lang))

    await state.update_data(lang=lang)
    await state.set_state(st)

    await call.answer()


@router.message(F.text, StateFilter(default_state))
async def cmd_bot(message: Message, state: FSMContext):
    uid = message.from_user.id
    user = await db.get_user_by_telegram(uid) or {}
    roles = user.get("roles") or []
    lang = user.get("language") or "🇺🇿 uz"
    role = pick_role(roles)
    caption_key = {
        ROLE_DIRECTOR: ("director", kb_director.main_menu, st_director.director.main_menu),
        ROLE_ADMIN:    ("admin",    kb_admin.main_menu,    st_admin.admin.main_menu),
        ROLE_BARBER:   ("barber",   kb_barber.main_menu,   st_barber.barber.main_menu),
        ROLE_CLIENT:   ("user",     kb_user.main_menu,     st_user.user.main_menu),
    }[role]
    role_key, kb_builder, st = caption_key
    caption = cf.get_text(lang, role_key, "message", "start_msg")
    photo = cf.get_logo_file()

    if photo:
        await bot.send_photo(
            chat_id=uid,
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=kb_builder(lang),
        )
    else:
        await bot.send_message(uid, caption, reply_markup=kb_builder(lang))

    await state.update_data(lang=lang)
    await state.set_state(st)


from handlers.user.handler import user_router
from handlers.barber.handler import barber_router
from handlers.admin.handler import admin_router
from handlers.director.handler import director_router

router.include_router(user_router)
router.include_router(barber_router)
router.include_router(admin_router)
router.include_router(director_router)
dp.include_router(router)