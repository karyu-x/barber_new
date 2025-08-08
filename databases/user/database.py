def select_user(tg_id: int) -> bool:
    users = [5012184829, 123456789]
    return tg_id in users

async def select_language(tg_id):
    return "🇺🇿 uz"

def all_users():
    return [5012184829, ]