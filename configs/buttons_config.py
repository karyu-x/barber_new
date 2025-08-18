from states.director import state as st
from keyboards.director import reply as kb_r
from keyboards.director import inline as kb_i
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
        "feedback": {
            "message": "feedback_msg",
            "keyboard": kb_r.feedback(lang),
            "state": st.director.feedback
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