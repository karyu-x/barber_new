import aiohttp

def select_director(tg_id: int) -> bool:
    directors = [5012184829, 888999000]
    return tg_id in directors

def rating_barbers():
    return {"Ali": 4.5, "Sherzod": 3.9, "Sanjar": 5.0, "Abdulaziz": 4.2}

def all_users():
    return [5012184829, 888999000]

async def get_all_users():
    return [
        {
            "id": 1,
            "telegram_id": 1001,
            "first_name": "Ali",
            "phone_number": "998901234567",
            "photo": None,
            "description": None,
            "rating": None,
            "default_from_hour": "09:00:00",
            "default_to_hour": "18:00:00",
            "roles": [1]
        },
        {
            "id": 2,
            "telegram_id": 1002,
            "first_name": "Karim",
            "phone_number": "998903241212",
            "photo": None,
            "description": None,
            "rating": None,
            "default_from_hour": "09:00:00",
            "default_to_hour": "18:00:00",
            "roles": [2]
        }
    ]


async def get_all_barbers():
    users = await get_all_users()
    return [item for item in users if 1 in item["roles"]]

async def get_barber_by_telegram_id(telegram_id):
    barbers = await get_all_barbers()
    return next((item for item in barbers if item["telegram_id"] == telegram_id), None)


########################## APIS ###########################

BASE_URL = "https://fd94f62807e9.ngrok-free.app"

async def fetch_json(url: str, method: str = "GET", **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, **kwargs) as resp:
            if resp.status == 200:
                try:
                    return await resp.json()
                except Exception:
                    return None
            else:
                print(f"[API ERROR] {url} -> {resp.status}")
                return None


# ==== USERS ====
async def get_users_all():
    url = f"{BASE_URL}/api/auth/users/"
    users = await fetch_json(url)
    if not users:
        return []

    data_base = []
    for user in users:
        telegram_id = user.get("telegram_id")
        if telegram_id:
            lang_code = str(user.get("language", "uz")).lower()
            language = "uz" if lang_code == "uz" else "🇷🇺 ru"

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


# ==== ROLES ====
async def get_directors_all():
    users = await get_users_all()
    return [u for u in users if 3 in u["roles"]]

async def get_admins_all():
    users = await get_users_all()
    return [u for u in users if 4 in u["roles"]]

async def get_barbers_all():
    users = await get_users_all()
    return [u for u in users if 1 in u["roles"]]


# ==== BARBER TYPES ====
async def get_barber_types(barber_id):
    url = f"{BASE_URL}/api/services/{barber_id}/get_barber_service_types/"
    return await fetch_json(url) or []


async def get_barber_type_by_id(type_id):
    url = f"{BASE_URL}/api/service-types/{type_id}/"
    return await fetch_json(url)


async def update_barber_type_by_id(type_id, type_name):
    url = f"{BASE_URL}/api/service-types/{type_id}/"
    payload = {"name": type_name}
    updated = await fetch_json(url, method="PATCH", json=payload)
    return updated is not None


# ==== BARBER SERVICES ====
async def get_barber_services(type_id):
    url = f"{BASE_URL}/api/services/{type_id}"
    return await fetch_json(url) or []


async def get_barber_service_by_id(service_id):
    url = f"{BASE_URL}/api/services/{service_id}/"
    return await fetch_json(url)


async def update_barber_service_by_id(service_id, data):
    url = f"{BASE_URL}/api/services/{service_id}/"
    updated = await fetch_json(url, method="PATCH", json=data)
    return updated is not None


# ==== CREATE BARBER ====
async def create_barber_by_phone(barber_phone, ids=1):
    url = f"{BASE_URL}/api/auth/users/{barber_phone}/add_role/{ids}"
    return await fetch_json(url, method="POST")


# ==== UPDATE BARBER ====
async def update_barber_by_tg_id(telegram_id, data):
    url = f"{BASE_URL}/api/auth/users/{telegram_id}/"
    updated = await fetch_json(url, method="PATCH", json=data)
    return updated is not None


################################################################

async def all_barber_types():
    return [
        {
            "id": 1,
            "name": "Detskaya strijka",
            "barber": 1
        },
        {
            "id": 2,
            "name": "Family strijka",
            "barber": 1
        },
        {
            "id": 3,
            "name": "Uxod za borodoy",
            "barber": 1
        },
        {
            "id": 4,
            "name": "Massaj",
            "barber": 1
        }
    ]


services = [
    {
        "id": 1,
        "name": "Fade strijka",
        "description": "Fade strijka haqida ma'lumot.",
        "duration": "30 minut",
        "price": 100000,
        "service_type": 1
    },
    {
        "id": 2,
        "name": "Premium strijka",
        "description": "Professional stilistdan VIP qirqim va styling.",
        "duration": "40 minut",
        "price": 150000,
        "service_type": 1
    }
]

async def get_service_by_id(service_id):
    for item in services:
        if service_id == item["id"]:
            return item

async def all_barber_services():
    return services



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
