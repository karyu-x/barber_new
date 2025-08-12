from states.director import state as st
from keyboards.director import reply as kb_r
from configs import functions as cf

async def get_main_buttons(lang):
    return {
        "notifications": {
            "message": "notifications_msg",
            "keyboard": kb_r.notifications(lang),
            "state": st.director.notifications
        },
        "bookings": {
            "message": "bookings_msg",
            "keyboard": kb_r.bookings(lang),
            "state": st.director.bookings
        },
        "settings": {
            "message": "settings_msg",
            "keyboard": kb_r.settings(lang),
            "state": st.director.settings
        },
        "clients": {
            "message": "clients_msg",
            "keyboard": kb_r.clients(lang),
            "state": st.director.clients
        },
        "analytics": {
            "message": "analytics_msg",
            "keyboard": kb_r.analytics(lang),
            "state": st.director.analytics
        },
        "finance": {
            "message": "finance_msg",
            "keyboard": kb_r.finance(lang),
            "state": st.director.finance
        },
        "journal": {
            "message": "journal_msg",
            "keyboard": kb_r.journal(lang),
            "state": st.director.journal
        },
        "feedback": {
            "message": "feedback_msg",
            "keyboard": kb_r.feedback(lang),
            "state": st.director.feedback
        },
        "language": {
            "message": "language_msg",
            "keyboard": kb_r.language(lang),
            "state": st.director.language
        }
        # "user_menu": {
        #     "message": "user_menu_msg",
        #     "keyboard": await kb_r.user_menu(lang),
        #     "state": st.director.user_menu
        # }
    }


NOTIFICATIONS_BUTTONS = {
    "input_text": {
        "message": "input_text_msg",
        "keyboard": kb_r.back_main,
        "state": st.director.input_text
    },
    "input_photo": {
        "message": "input_photo_msg",
        "keyboard": kb_r.back_main,
        "state": st.director.input_photo
    },
    "input_button": {
        "message": "input_button_msg",
        "keyboard": kb_r.back_main,
        "state": st.director.input_button
    },
    "check_post": {
        "message": "check_post_msg",
        "keyboard": kb_r.check_post,
        "state": st.director.check_post
    },
    "back": {
        "message": "main_menu_msg",
        "keyboard": kb_r.main_menu,
        "state": st.director.main_menu
    }
}

BOOKINGS_BUTTONS = {
    "today_books": {
        "message": "today_books_msg",
        "keyboard": kb_r.today_books,
        "state": st.director.today_books
    },
    "other_day_books": {
        "message": "other_day_books_msg",
        "keyboard": kb_r.other_day_books,
        "state": st.director.other_day_books
    },
    "cancel_books": {
        "message": "cancel_books_msg",
        "keyboard": kb_r.cancel_books,
        "state": st.director.cancel_books
    },
    "reschedule_books": {
        "message": "reschedule_books_msg",
        "keyboard": kb_r.reschedule_books,
        "state": st.director.reschedule_books
    },
    "back": {
        "message": "main_menu_msg",
        "keyboard": kb_r.main_menu,
        "state": st.director.main_menu
    }
}

async def get_setting_buttons(lang):
    return {
        "services_prices": {
            "message": "services_prices_msg",
            "keyboard": await kb_r.services_prices(lang),
            "state": st.director.services_prices
        },
        "barbers": {
            "message": "barbers_msg",
            "keyboard": await kb_r.barbers(lang),
            "state": st.director.barbers
        },
        "admins": {
            "message": "admins_msg",
            "keyboard": await kb_r.admins(lang),
            "state": st.director.admins
        },
        "language": {
            "message": "language_msg",
            "keyboard": kb_r.language(lang),
            "state": st.director.language
        },
        "back": {
            "message": "main_menu_msg",
            "keyboard": kb_r.main_menu(lang),
            "state": st.director.main_menu
        }
    }

AVAILABLE_BUTTONS = [
    "notifications",
    "bookings",
    "settings",
    "clients",
    "analytics",
    "finance",
    "journal",
    "feedback",
    "user_menu"
]

def button_title(lang: str, role: str, button_id: str) -> str:
    return cf.get_text(lang, role, "button", button_id)