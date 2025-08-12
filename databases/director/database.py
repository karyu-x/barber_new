import aiohttp
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://fd94f62807e9.ngrok-free.app"

session: aiohttp.ClientSession | None = None

async def get_session():
    global session
    if session is None or session.closed:
        session = aiohttp.ClientSession()
    return session


async def api_request(method: str, endpoint: str, json=None, params=None):
    url = f"{BASE_URL}{endpoint}"
    sess = await get_session()
    try:
        async with sess.request(method, url, json=json, params=params) as resp:
            try:
                data = await resp.json()
            except aiohttp.ContentTypeError:
                data = await resp.text()

            logger.info(f"[API] {method} {resp.url} | Status: {resp.status}")
            if json:
                logger.info(f"Payload: {json}")
            if params:
                logger.info(f"Params: {params}")
            logger.info(f"Response: {data}")

            return data if resp.status == 200 else None
    except Exception as e:
        logger.error(f"API request error {method} {url}: {e}")
        return None




### ==== USERS ==== ###
async def get_users_all():
    # users = await api_request(
    #     method="GET", 
    #     endpoint="/api/auth/users/"
    # )
    # if not users:
    #     return []

    # data_base = []
    # for user in users:
    #     telegram_id = user.get("telegram_id")
    #     if telegram_id:
    #         lang_code = user.get("language").lower()
    #         language = "🇺🇿 uz" if lang_code == "uz" else "🇷🇺 ru"
    #         data_base.append({
    #             "id": user.get("id"),
    #             "telegram_id": telegram_id,
    #             "first_name": user.get("first_name"),
    #             "phone_number": user.get("phone_number"),
    #             "language": language,
    #             "photo": user.get("photo"),
    #             "description": user.get("description"),
    #             "rating": user.get("rating"),
    #             "default_from_hour": user.get("default_from_hour"),
    #             "default_to_hour": user.get("default_to_hour"),
    #             "roles": user.get("roles", [])
    #         })
    # return data_base
    return [
        {"id": 1, "telegram_id": 1001, "first_name": "Ali", "phone_number": "998901234567", "language": "🇺🇿 uz", "photo": None, "description": "Yaxshi ishchi", "rating": 4.5, "default_from_hour": "09:00:00", "default_to_hour": "18:00:00", "roles": [1]},
        {"id": 2, "telegram_id": 1002, "first_name": "Karim", "phone_number": "998903241212", "language": "🇺🇿 uz", "photo": None, "description": "", "rating": None, "default_from_hour": "09:00:00", "default_to_hour": "18:00:00", "roles": [2]},
        {"id": 3, "telegram_id": 5012184829, "first_name": "Shoxa", "phone_number": "998900123912", "language": "🇺🇿 uz", "photo": None, "description": "", "rating": None, "default_from_hour": "09:00:00", "default_to_hour": "18:00:00", "roles": [3]},
        {"id": 4, "telegram_id": 1004, "first_name": "Samandar", "phone_number": "998900210160", "language": "🇺🇿 uz", "photo": None, "description": "", "rating": None, "default_from_hour": "09:00:00", "default_to_hour": "18:00:00", "roles": [4]},
        {"id": 5, "telegram_id": 1005, "first_name": "Sulton", "phone_number": "998900210123", "language": "🇺🇿 uz", "photo": None, "description": "", "rating": None, "default_from_hour": "09:00:00", "default_to_hour": "18:00:00", "roles": [1]},
        {"id": 6, "telegram_id": 1006, "first_name": "Umar", "phone_number": "998900211234", "language": "🇺🇿 uz", "photo": None, "description": "", "rating": None, "default_from_hour": "09:00:00", "default_to_hour": "18:00:00", "roles": [4]},
    ]


async def get_user_by_telegram(telegram_id):
    users = await get_users_all()
    return next((item for item in users if item["telegram_id"] == telegram_id), None)

################################# ==== ROLES ==== #################################

# == DIRECTORS == #
async def get_directors_all():
    users = await get_users_all()
    return [u for u in users if 3 in u["roles"]]

async def create_director_by_phone(director_phone):
    data = {"roles": [3, 2]}
    return await api_request("POST", f"/api/auth/users/{director_phone}/add_role", json=data)

async def get_director_by_id(director_id):
    directors = await get_directors_all()
    return next((item for item in directors if item["telegram_id"] == director_id), None)

async def update_director_by_id(director_id, data):
    return await api_request("PATCH", f"/api/auth/users/{director_id}", json=data)

async def delete_director_by_id(director_id):
    return await api_request("DELETE", f"/api/auth/users/{director_id}/remove_role")


# == ADMINS == #
async def get_admins_all():
    users = await get_users_all()
    return [u for u in users if 4 in u["roles"]]

async def create_admin_by_phone(admin_phone):
    data = {"roles": [4, 2]}
    return await api_request("POST", f"/api/auth/users/{admin_phone}/add_role", json=data)

async def get_admin_by_id(admin_id):
    admins = await get_admins_all()
    return next((item for item in admins if item["telegram_id"] == admin_id), None)

async def update_admin_by_id(admin_id, data):
    return await api_request("PATCH", f"/api/auth/users/{admin_id}", json=data)

async def delete_admin_by_id(admin_id):
    return await api_request("DELETE", f"/api/auth/users/{admin_id}/remove_role")


# == BARBERS == #
async def get_barbers_all():
    users = await get_users_all()
    return [u for u in users if 1 in u["roles"]]

async def create_barber_by_phone(barber_phone):
    data = {"roles": [1, 2]}
    return await api_request("POST", f"/api/auth/users/{barber_phone}/add_role", json=data)

async def get_barber_by_id(barber_id):
    barbers = await get_barbers_all()
    return next((item for item in barbers if item["telegram_id"] == barber_id), None)

async def update_barber_by_id(barber_id, data):
    return await api_request("PATCH", f"/api/auth/users/{barber_id}", json=data)

async def delete_barber_by_id(barber_id):
    return await api_request("DELETE", f"/api/auth/users/{barber_id}/remove_role")


# == CLIENTS == #
async def get_clients_all():
    users = await get_users_all()
    return [u for u in users if 2 in u["roles"]]

async def get_client_by_telegram_id(telegram_id):
    clients = await get_clients_all()
    return next((item for item in clients if item["telegram_id"] == telegram_id), None)


################################# ==== BARBER TYPES ==== #################################

async def get_barber_types(barber_id):
    # return await api_request(
    #     method="GET",
    #     endpoint=f"/api/service-types/{barber_id}"
    # ) or []
    return [
        {"id": 1, "name": "Detskaya strijka", "barber": 1001},
        {"id": 2, "name": "Family strijka", "barber": 1005},
        {"id": 3, "name": "Uxod za borodoy", "barber": 1001},
        {"id": 4, "name": "Massaj", "barber": 1005}
    ]

async def create_barber_type(data):
    return await api_request("POST", "/api/service-types/", json=data)

async def get_barber_type_by_id(barber_id, type_id):
    types = await get_barber_types(barber_id)
    return next((item for item in types if item["id"] == type_id), None)

async def update_barber_type_by_id(type_id, data):
    return await api_request("PATCH", f"/api/service-types/{type_id}/", json=data)

async def delete_barber_type_by_id(type_id):
    return await api_request("DELETE", f"/api/service-types/{type_id}/")


################################# ==== BARBER SERVICES ==== #################################

# == SERVICES == #
async def get_barber_services(type_id):
    # return await api_request("GET", f"/api/services/{type_id}/get_services/")
    return [
        {"id": 1, "name": "Fade strijka", "description": "Fade strijka haqida ma'lumot.", "duration": "30 minut", "price": 100000, "service_type": 1},
        {"id": 2, "name": "Premium strijka", "description": "Professional stilistdan VIP qirqim va styling.", "duration": "40 minut", "price": 150000, "service_type": 1}
    ]

async def create_barber_service(data):
    return await api_request("POST", "/api/services/", json=data)

async def get_barber_service_by_id(type_id, service_id):
    services = await get_barber_services(type_id)
    return next((item for item in services if item["id"] == service_id), None)

async def update_barber_service_by_id(service_id, data):
    return await api_request("PATCH", f"/api/services/{service_id}/", json=data)

async def delete_barber_service_by_id(service_id):
    return await api_request("DELETE", f"/api/services/{service_id}/")

################################################################

def rating_barbers():
    return {"Ali": 4.5, "Sherzod": 3.9, "Sanjar": 5.0, "Abdulaziz": 4.2}

async def all_feedbacks():
    return [
        {
            "type": "Barber",
            "barber_name": "Ali",
            "service": 5.0,
            "communication": 3.5,
            "clean": "-",
            "price": "-",
            "text": "Yaxshi soch olarkan",
            "date": "2025-08-01",
            "client": {
                "name": "Javlon",
                "phone": "+998901234567"
            }
        },
        {
            "type": "Salon",
            "barber_name": "-",
            "service": 4.8,
            "communication": 4.2,
            "clean": 4.9,
            "price": 4.5,
            "text": "Toza va zamonaviy salon. Narxlari ham o‘rtacha.",
            "date": "2025-08-01",
            "client": {
                "name": "Aziza",
                "phone": "+998998877665"
            }
        },
        {
            "type": "Barber",
            "barber_name": "Sanjar",
            "service": 4.5,
            "communication": 4.0,
            "clean": "-",
            "price": "-",
            "text": "Juda muloyim va o‘z ishining ustasi.",
            "date": "2025-07-30",
            "client": {
                "name": "Bekzod",
                "phone": "+998935554433"
            }
        },
        {
            "type": "Barber",
            "barber_name": "Sherzod",
            "service": 3.8,
            "communication": 4.0,
            "clean": "-",
            "price": "-",
            "text": "Yaxshi, lekin vaqtida chaqirmadi.",
            "date": "2025-07-28",
            "client": {
                "name": "Dilshod",
                "phone": "+998911112233"
            }
        },
        {
            "type": "Salon",
            "barber_name": "-",
            "service": 4.2,
            "communication": 4.5,
            "clean": 5.0,
            "price": 4.0,
            "text": "Hammasi zo’r! Salonda hushmuomalalik yuqori.",
            "date": "2025-07-26",
            "client": {
                "name": "Madina",
                "phone": "+998902223344"
            }
        }
    ]