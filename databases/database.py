import aiohttp, asyncio, logging
from decouple import config

logger = logging.getLogger(__name__)

BASE_URL = config("BASE_URL")

session: aiohttp.ClientSession | None = None

async def get_session() -> aiohttp.ClientSession:
    global session
    if session is None or session.closed:
        session = aiohttp.ClientSession()
    return session

async def close_session():
    global session
    if session and not session.closed:
        await session.close()
        session = None


async def api_request(method: str, endpoint: str, json=None, params=None, timeout: float = 10):
    url = f"{BASE_URL}{endpoint}"
    sess = await get_session()
    req_timeout = aiohttp.ClientTimeout(total=timeout)

    try:
        async with sess.request(method, url, json=json, params=params, timeout=req_timeout) as resp:
            status = resp.status

            if status == 204:
                logger.info(f"[API] {method} {url} | {status} No Content")
                return None

            content_type = resp.headers.get("Content-Type", "")
            body = None
            if "application/json" in content_type.lower():
                try:
                    body = await resp.json()
                except aiohttp.ContentTypeError:
                    body = await resp.text()
            else:
                body = await resp.text()

            if 200 <= status < 300:
                logger.info(f"[API] {method} {resp.url} | {status}")
                if json:
                    logger.info(f"Payload: {json}")
                if params:
                    logger.info(f"Params: {params}")
                logger.info(f"Response: {body}")
                return body

            logger.error(f"[API] {method} {url} | HTTP error: {status} | Body: {body}")
            return None

    except asyncio.TimeoutError:
        logger.error(f"[API] {method} {url} | Timeout after {timeout}s")
        return None
    except aiohttp.ClientResponseError as e:
        logger.error(f"[API] {method} {url} | ClientResponseError: {e.status} {e.message}")
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


async def get_user_by_id(telegram_id=None, id=None, phone=None):
    user = None
    if id is not None:
        user = await api_request(method="GET", endpoint=f"/api/auth/users/get_user_data/{id}/")
    elif telegram_id is not None:
        user = await api_request(method="GET", endpoint=f"/api/auth/users/if_exists/{telegram_id}/")
    elif phone is not None:
        users = await get_users_all()
        for u in users:
            if u.get("phone_number") == phone:
                user = u
                break

    if not user:
        return {}

    lang_code = user.get("language", "").lower()
    language = "🇺🇿 uz" if lang_code == "uz" else "🇷🇺 ru"
    user["language"] = language
    return user

async def update_user_by_id(user_id, data):
    return await api_request("PATCH", f"/api/auth/users/{user_id}/", json=data)

################################# ==== ROLES ==== #################################

# == DIRECTORS == #
async def get_directors_all():
    role = 3
    return await api_request(method="GET", endpoint=f"/api/auth/users/by-role/{role}/")

async def create_director_by_phone(director_phone):
    data = {"role_id": 3}
    return await api_request("PATCH", f"/api/auth/users/add_role/{director_phone}/", json=data)

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

async def update_admin_by_id(admin_id, data):
    return await api_request("PATCH", f"/api/auth/users/{admin_id}/", json=data)

async def delete_admin_by_phone(admin_phone):
    data = {"role_id": 4}
    return await api_request("PATCH", f"/api/auth/users/remove_role/{admin_phone}/", json=data)


# == BARBERS == #
async def get_barbers_all():
    role = 1
    return await api_request(method="GET", endpoint=f"/api/auth/users/by-role/{role}/")

async def get_barber_rating_by_id(barber_id):
    return await api_request("GET", f"/api/auth/users/get_rating_by_barber_id/{barber_id}/")

async def get_barber_hours_by_telegram(telegram_id):
    return await api_request("GET", f"/api/booking/working-hours/by-telegram/{telegram_id}/")

async def create_barber_by_phone(barber_phone):
    data = {"role_id": 1}
    return await api_request("PATCH", f"/api/auth/users/add_role/{barber_phone}/", json=data)

async def update_barber_by_id(barber_id, data):
    return await api_request("PATCH", f"/api/auth/users/{barber_id}/", json=data)

async def update_working_hours_by_id(barber_id, data):
    return await api_request("PATCH", f"/api/booking/working-hours/barber/{barber_id}/set-hours/", json=data)

async def delete_barber_by_phone(barber_phone):
    data = {"role_id": 1}
    return await api_request("PATCH", f"/api/auth/users/remove_role/{barber_phone}/", json=data)


# == CLIENTS == #
async def get_clients_all():
    role = 2
    return await api_request(method="GET", endpoint=f"/api/auth/users/by-role/{role}/")

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

async def get_barber_bookings(barber_id, date):
    return await api_request("GET", f"/api/booking/get_bookings/{barber_id}/{date}/") or []


async def get_booking_by_id(booking_id):
    return await api_request("GET", f"/api/booking/get_bookings_by_id/{booking_id}/")


async def get_active_booking_by_client_phone(phone_number):
    return await api_request("GET", f"/api/booking/get_active_booking/{phone_number}/")


async def booking_cancel_by_id(booking_id, tg_id, reason):
    data = {
        "telegram_id": tg_id,
        "cancel_reason": reason
    }
    return await api_request("POST", f"/api/booking/{booking_id}/cancel/", json=data)


async def booking_forward_by_id(booking_id, barber_id):
    data = { "barber": barber_id }
    return await api_request("PATCH", f"/api/booking/{booking_id}/", json=data)


################################# ==== BARBER TYPES ==== #################################

async def get_barber_types_and_services(barber_id):
    return await api_request("GET", f"/api/service-types/by-telegram/{barber_id}") or []

async def get_barber_types(barber_id):
    return await api_request("GET", f"/api/service-types/only-type-by-telegram/{barber_id}/") or []

async def create_barber_type(data):
    return await api_request("POST", "/api/service-types/", json=data)

async def get_barber_type_by_id(type_id):
    return await api_request("GET", f"/api/service-types/{type_id}/")

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

async def get_barber_service_by_id(service_id):
    return await api_request("GET", f"/api/services/{service_id}/") or None

async def update_barber_service_by_id(service_id, data):
    return await api_request("PATCH", f"/api/services/{service_id}/", json=data)

async def delete_barber_service_by_id(service_id):
    return await api_request("DELETE", f"/api/services/{service_id}/")

################################################################

async def create_barber_break(datas):
    return await api_request("POST", "/api/break/", json=datas)

async def get_barber_breaks(barber_id):
    return await api_request("GET", f"/api/break/get_breaks_by_barber_id/{barber_id}/") or []

async def get_barber_break_by_id(break_id, barber_id):
    return await api_request("GET", f"/api/break/{break_id}/barber_detail/{barber_id}/")

async def update_barber_break_by_id(break_id, data):
    return await api_request("PATCH", f"/api/break/{break_id}/", json=data)

async def delete_barber_break_by_id(break_id):
    return await api_request("DELETE", f"/api/break/{break_id}/")


#########################################################################################################


async def create_user(telegram_id, phone, first_name, language):
    url = f"{BASE_URL}/api/auth/register/"
    language = language.split(' ')[1]
    payload = {
        "telegram_id": telegram_id,
        "phone_number": phone,
        "first_name": first_name,
        "language": language
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:

                if response.status in [200, 201]:
                    print("User created successfully.")
                    return await response.json()

                elif response.status == 400:
                    error_data = await response.json()
                    if 'telegram_id' in error_data and "already exist" in error_data['telegram_id'][0]:
                        return None
                    else:
                        return False

                return f"An error occurred: {response.status}"

    except aiohttp.ClientError as e:
        print(f"A network error occurred: {e}")
        return "Network error."



async def is_user_exists(telegram_id):
    url = f"{BASE_URL}/api/auth/users/if_exists/{telegram_id}/"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:

                if response.status == 200:
                    return await response.json()

                elif response.status == 404:
                    print("User does not exist.")
                    return False

                else:
                    print(f"Unexpected error: {response.status}")
                    return f"An error occurred: {response.status}"

    except aiohttp.ClientError as e:
        print(f"A network error occurred: {e}")
        return "Network error."



async def user_booking_history(tg_id):
    url = f"{BASE_URL}/api/booking/booking-history/{tg_id}/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data

                elif response.status == 404:
                    return await response.json()

                else:
                    return f"An error occurred: {response.status}"

    except aiohttp.ClientError as e:
        print(f"A network error occurred: ")
        return f"Network error:{e}"



async def all_barbers_info(by_role):
    url = f"{BASE_URL}/api/auth/users/by-role/{by_role}/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data

                elif response.status == 404:
                    return await response.json()

                else:
                    return f"An error occurred: {response.status}"

    except aiohttp.ClientError as e:
        print(f"A network error occurred: ")
        return f"Network error:{e}"



async def barber_service_type(tg_id):
    url = f"{BASE_URL}/api/service-types/only-type-by-telegram/{tg_id}/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data

                elif response.status == 404:
                    return await response.json()

                else:
                    return f"An error occurred: {response.status}"

    except aiohttp.ClientError as e:
        print(f"A network error occurred: ")
        return f"Network error:{e}"


async def get_time_api(date, barber_id, service_id):
    return await api_request("GET", f"/api/booking/available-slots/{date}/{barber_id}/{service_id}/")
    

########################################### BOOKINGS ###########################################

async def create_booking(datas):
    return await api_request("POST", "/api/booking/", json=datas)

async def submit_booking_rating(barber_id, user_id, score):
    payload = { "barber": barber_id, "client": user_id, "rating": score }
    return await api_request("POST", f"/api/auth/users/post_rating/", json=payload)

async def submit_booking_comment(booking_id, comment):
    return await api_request("PATCH", f"/api/booking/{booking_id}/", json={"notes": comment})

########################################### ANALYTICS ###########################################

async def get_weekly_analytics():
    return await api_request("GET", "/api/weekly/")


async def get_barber_activities():
    return await api_request("GET", "/api/weekly/barber_activity/")


async def get_barber_ratings():
    return await api_request("GET", "/api/auth/users/get_rating/")


async def get_top_services():
    return await api_request("GET", "/api/weekly/top_services/")