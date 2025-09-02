from aiogram import Bot, Router, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.filters import StateFilter
from decouple import config

from configs import functions as cf
from keyboards import reply as kb
from states import state as st
from databases import database as db

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
    user = await db.get_user_by_id(telegram_id=uid)

    if not user:  
        await call.bot.send_message(uid, cf.translations["start"], reply_markup=kb.start_key())
        await state.set_state(st.user.language)  
        await call.answer()
        return

    roles = user.get("roles")
    lang = user.get("language") or "🇺🇿 uz"
    role = pick_role(roles)
    caption_key = {
        ROLE_DIRECTOR: ("director", kb.dr_main_menu(lang), st.director.main_menu),
        ROLE_ADMIN:    ("director", kb.ad_main_menu(lang, uid), st.admin.main_menu),
        ROLE_BARBER:   ("barber", kb.br_main_menu(lang), st.barber.main_menu),
        ROLE_CLIENT:  ("client", kb.us_main_menu(lang, user.get("roles")), st.user.main_menu)
    }[role]
    _, kb_builder, sts = caption_key
    caption = cf.get_text(lang, "start_msg")
    photo = cf.get_logo_file()

    await call.message.delete()

    if photo:
        await call.bot.send_photo(
            chat_id=uid,
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=kb_builder,
        )
    else:
        await call.bot.send_message(uid, caption, reply_markup=kb_builder)

    await state.update_data(lang=lang, my_infos=user)
    await state.set_state(sts)

    await call.answer()


@router.message(F.text, StateFilter(default_state))
async def cmd_bot(message: Message, state: FSMContext):
    uid = message.from_user.id
    user = await db.get_user_by_id(telegram_id=uid)

    if not user: 
        await message.bot.send_message(uid, cf.translations["start"], reply_markup=kb.start_key())
        await state.set_state(st.user.language)  
        return

    roles = user.get("roles")
    lang = user.get("language") or "🇺🇿 uz"
    role = pick_role(roles)
    caption_key = {
        ROLE_DIRECTOR: ("director", kb.dr_main_menu(lang), st.director.main_menu),
        ROLE_ADMIN:    ("director", kb.ad_main_menu(lang, uid), st.admin.main_menu),
        ROLE_BARBER:   ("barber", kb.br_main_menu(lang), st.barber.main_menu),
        ROLE_CLIENT:  ("client", kb.us_main_menu(lang, user.get("roles")), st.user.main_menu)
    }[role]
    _, kb_builder, sts = caption_key
    caption = cf.get_text(lang, "start_msg")
    photo = cf.get_logo_file()

    if photo:
        await bot.send_photo(
            chat_id=uid,
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=kb_builder,
        )
    else:
        await bot.send_message(uid, caption, reply_markup=kb_builder)

    await state.update_data(lang=lang, my_infos=user)
    await state.set_state(sts)


from middlewares.ban import BanMiddleware  
from .cl_handler import user_router
from .br_handler import barber_router
from .ad_handler import admin_router
from .dr_handler import director_router
from .rate_booking import rate_router

router.include_router(rate_router)
router.include_router(user_router)
router.include_router(barber_router)
router.include_router(admin_router)
router.include_router(director_router)

ban_mw = BanMiddleware(ttl_seconds=45)
router.message.middleware(ban_mw)
router.callback_query.middleware(ban_mw)

dp.include_router(router)