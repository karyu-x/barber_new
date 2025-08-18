import aiohttp
import logging

logger = logging.getLogger(__name__)

BASE_URL =  "http://20.124.93.156:8080"

session: aiohttp.ClientSession | None = None

async def get_session():
    global session
    if session is None or session.closed:
        session = aiohttp.ClientSession()
    return session


async def api_request(method: str, endpoint: str, json=None, params=None, timeout=10):
    url = f"{BASE_URL}{endpoint}"
    sess = await get_session()

    try:
        async with sess.request(method, url, json=json, params=params, timeout=timeout) as resp:
            if resp.status == 204:
                logger.info(f"[API] {method} {url} | Status: {resp.status} | No content returned")
                return None

            if resp.status == 200:
                try:
                    data = await resp.json()
                except aiohttp.ContentTypeError:
                    data = await resp.text()

                if not data:
                    logger.warning(f"[API] {method} {url} | Status: {resp.status} | No content returned")
                    return None

                logger.info(f"[API] {method} {resp.url} | Status: {resp.status}")
                if json:
                    logger.info(f"Payload: {json}")
                if params:
                    logger.info(f"Params: {params}")
                logger.info(f"Response: {data}")

                return data

            logger.error(f"[API] {method} {url} | Error: {resp.status}")
            return None

    except aiohttp.ClientTimeout:
        logger.error(f"[API] {method} {url} | Timeout occurred after {timeout} seconds")
        return None
    except aiohttp.ClientError as e:
        logger.error(f"[API] {method} {url} | ClientError: {e}")
        return None
    except Exception as e:
        logger.error(f"[API] {method} {url} | Unexpected error: {e}")
        return None


### ==== USERS ==== ###
async def get_users_all():
    users = await api_request(
        method="GET", 
        endpoint="/api/auth/users/"
    )
    if not users:
        return []

    data_base = []
    for user in users:
        telegram_id = user.get("telegram_id")
        if telegram_id:
            lang_code = user.get("language").lower()
            language = "🇺🇿 uz" if lang_code == "uz" else "🇷🇺 ru"
            data_base.append({
                "id": user.get("id"),
                "telegram_id": telegram_id,
                "first_name": user.get("first_name"),
                "phone_number": user.get("phone_number"),
                "language": language,
                "photo": user.get("photo"),
                "description": user.get("description"),
                "rating": user.get("rating"),
                "default_from_hour": user.get("default_from_hour"),
                "default_to_hour": user.get("default_to_hour"),
                "roles": user.get("roles", [])
            })
    return data_base


async def get_user_by_telegram(telegram_id):
    user = await api_request(method="GET", endpoint=f"/api/auth/users/if_exists/{telegram_id}/")

    if user is None:
        return {}
    
    lang_code = user.get("language").lower()
    language = "🇺🇿 uz" if lang_code == "uz" else "🇷🇺 ru"
    user["language"] = language

    return user

################################# ==== ROLES ==== #################################

# == DIRECTORS == #
async def get_directors_all():
    role = 3
    return await api_request(method="GET", endpoint=f"/api/auth/users/by-role/{role}/")

async def create_director_by_phone(director_phone):
    data = {"role_id": 3}
    return await api_request("PATCH", f"/api/auth/users/add_role/{director_phone}/", json=data)

async def get_director_by_telegram_id(telegram_id):
    user = await get_user_by_telegram(telegram_id)
    if 3 in user.get("roles"):
        return user

async def update_director_by_id(director_id, data):
    return await api_request("PATCH", f"/api/auth/users/{director_id}/", json=data)

async def delete_director_by_phone(director_phone):
    data = {"role_id": 3}
    return await api_request("PATCH", f"/api/auth/users/remove_role/{director_phone}/", json=data)


# == ADMINS == #
async def get_admins_all():
    role = 4
    return await api_request(method="GET", endpoint=f"/api/auth/users/by-role/{role}/")

async def create_admin_by_phone(admin_phone):
    data = {"role_id": 4}
    return await api_request("PATCH", f"/api/auth/users/add_role/{admin_phone}/", json=data)

async def get_admin_by_telegram_id(telegram_id):
    user = await get_user_by_telegram(telegram_id)
    if 4 in user.get("roles"):
        return user

async def update_admin_by_id(admin_id, data):
    return await api_request("PATCH", f"/api/auth/users/{admin_id}/", json=data)

async def delete_admin_by_phone(admin_phone):
    data = {"role_id": 4}
    return await api_request("PATCH", f"/api/auth/users/remove_role/{admin_phone}/", json=data)


# == BARBERS == #
async def get_barbers_all():
    role = 1
    return await api_request(method="GET", endpoint=f"/api/auth/users/by-role/{role}/")

async def create_barber_by_phone(barber_phone):
    data = {"role_id": 1}
    return await api_request("PATCH", f"/api/auth/users/add_role/{barber_phone}/", json=data)

async def get_barber_by_telegram_id(telegram_id):
    user = await get_user_by_telegram(telegram_id)
    if 1 in user.get("roles"):
        return user

async def update_barber_by_id(barber_id, data):
    return await api_request("PATCH", f"/api/auth/users/{barber_id}/", json=data)

async def delete_barber_by_phone(barber_phone):
    data = {"role_id": 1}
    return await api_request("PATCH", f"/api/auth/users/remove_role/{barber_phone}/", json=data)


# == CLIENTS == #
async def get_clients_all():
    role = 2
    return await api_request(method="GET", endpoint=f"/api/auth/users/by-role/{role}/")
    
async def get_client_by_telegram_id(telegram_id):
    user = await get_user_by_telegram(telegram_id)
    if 2 in user.get("roles"):
        return user
    
async def get_client_by_phone(client_phone):
    clients = await get_clients_all()
    for c in clients:
        if c.get("phone_number") == client_phone:
            return c

async def ban_client_by_phone(client_phone):
    data = {"role_id": 5}
    return await api_request("PATCH", f"/api/auth/users/add_role/{client_phone}/", json=data)

async def unban_client_by_phone(client_phone):
    data = {"role_id": 5}
    return await api_request("PATCH", f"/api/auth/users/remove_role/{client_phone}/", json=data)


################################# ==== BARBER BOOKINGS ==== #################################

async def get_barber_bookings(barber_telegram_id):
    return await api_request("GET", f"/api/booking/get_booking/{barber_telegram_id}/") or []


################################# ==== BARBER TYPES ==== #################################

async def get_barber_types(barber_id):
    return await api_request(
        method="GET",
        endpoint=f"/api/service-types/only-type-by-telegram/{barber_id}/"
    ) or []

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
    return await api_request("GET", f"/api/services/{type_id}/get_services/") or []

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