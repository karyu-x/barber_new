import random, asyncio
from datetime import datetime, timezone, timedelta

from aiogram import Router, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from databases import database as db
from configs import functions as cf
from configs.survey_storage import remove
from states import state as st
from keyboards import reply as kb

rate_router = Router()
router = rate_router

class SurveyStates(StatesGroup):
    rate_comment = State()
    waiting_comment = State()

def stars_kb(booking_id: int, barber_id: int, user_id: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="⭐", callback_data=f"rate:{booking_id}_{barber_id}_{user_id}:1"),
        InlineKeyboardButton(text="⭐⭐", callback_data=f"rate:{booking_id}_{barber_id}_{user_id}:2"),
        InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"rate:{booking_id}_{barber_id}_{user_id}:3"),
        InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"rate:{booking_id}_{barber_id}_{user_id}:4"),
        InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"rate:{booking_id}_{barber_id}_{user_id}:5"), width=1
    )
    return kb.as_markup()

def comment_kb(lang) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[([InlineKeyboardButton(text=cf.get_text(lang, "survey", "comment_button"), callback_data="comment")])])


TZ_TASHKENT = timezone(timedelta(hours=5))

def _iso_to_local(s: str) -> datetime:
    s = s.strip()
    if s.endswith("Z"):
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    else:
        dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ_TASHKENT)
    return dt.astimezone(TZ_TASHKENT)

async def send_survey_message(bot, state: FSMContext, user_id: int, telegram_id: int, booking_id: int, barber_id: int, lang: str):
    booking = await db.get_booking_by_id(booking_id)

    if booking:
        start_local = _iso_to_local(booking.get("start_time"))
        end_local   = _iso_to_local(booking.get("end_time"))
        time_str = f"{start_local:%d.%m.%Y %H:%M}–{end_local:%H:%M}"
        barber = await db.get_user_by_id(id=barber_id)
        service = await db.get_barber_service_by_id(booking.get("service_id"))

        barber_name = (barber.get("first_name") or f"#{barber_id}")
        service_name = (service.get("name") or "—")
        price = service.get("price")
        price_str = f"{price:,}".replace(",", " ") + " UZS" if isinstance(price, (int, float)) else "—"

        header = cf.get_text(lang, "survey", "visit_card_title")
        ask = cf.get_text(lang, "survey", "ask_rating")

        text = (
            f"{header}\n\n"
            f"📅 <b>{time_str}</b>\n"
            f"🧔 <b>Barber/Барбер:</b> {barber_name}\n"
            f"🛎 <b>Xizmat/Услуга:</b> {service_name}\n"
            f"💵 <b>Narx/Цена:</b> {price_str}\n\n"
            f"{ask}"
        )
        parse_mode = "HTML"

    else:
        text = cf.get_text(lang, "survey", "ask_rating")
        parse_mode = None

    msg = await bot.send_message(user_id, random.choice(cf.SECRET_MESSAGES), reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.025)
    try:
        await msg.delete()
    except Exception:
        pass

    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode=parse_mode,
        reply_markup=stars_kb(booking_id, barber_id, user_id)
    )
    await state.set_state(SurveyStates.rate_comment)


@router.callback_query(F.data.regexp(r"^rate:(\d+)_(\d+)_(\d+):([1-5])$"), SurveyStates.rate_comment)
async def receive_rating(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    _, ids, score_s = callback.data.split(":")
    booking_s, barber_s, user_s = ids.split("_")
    booking_id = int(booking_s)
    barber_id  = int(barber_s)
    user_id    = int(user_s)
    score      = int(score_s)

    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")

    ok = await db.submit_booking_rating(barber_id=barber_id, user_id=user_id, score=score)
    if ok:
        rate_msg = cf.get_text(lang, "survey", "thank_you_rate").format(score=score)
        await callback.message.edit_text(rate_msg, reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=cf.get_text(lang, "survey", "comment_button"), callback_data="comment")]]
        ))
        await remove(booking_id)
        await state.update_data(survey_booking_id=booking_id)
        await state.set_state(SurveyStates.waiting_comment)
    else:
        await callback.message.edit_text(cf.get_text(lang, "survey", "error"))


@router.callback_query(F.data == "comment", SurveyStates.waiting_comment)
async def ask_comment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    await callback.message.edit_text(cf.get_text(lang, "survey", "comment"), reply_markup=None)
    await state.set_state(SurveyStates.waiting_comment)


@router.message(SurveyStates.waiting_comment)
async def save_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "🇺🇿 uz")
    booking_id = int(data["survey_booking_id"])
    text = message.text.strip() if message.text else ""

    ok = await db.submit_booking_comment(booking_id=booking_id, comment=text)
    if ok:
        await message.answer(cf.get_text(lang, "survey", "thank_you_comment"), reply_markup=kb.us_main_menu(lang, data.get("my_infos", {}).get("roles", [])))
    else:
        await message.answer(cf.get_text(lang, "survey", "error"), reply_markup=kb.us_main_menu(lang, data.get("my_infos", {}).get("roles", [])))
    await state.set_state(st.user.main_menu)
