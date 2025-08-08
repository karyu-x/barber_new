def select_director(tg_id: int) -> bool:
    directors = [5012184829, 888999000]
    return tg_id in directors

def rating_barbers():
    return {"Ali": 4.5, "Sherzod": 3.9, "Sanjar": 5.0, "Abdulaziz": 4.2}

def all_users():
    return [5012184829, 888999000]


async def all_barbers_name():
    return [
        {
            "tg_id": 1,
            "name": "Ali"
        },
        {
            "tg_id": 2,
            "name": "Sherzod"
        },
        {
            "tg_id": 3,
            "name": "Sanjar"
        }
    ]

async def get_all_users():
    return [
        {
            "id": 1,
            "telegram_id": 1001,
            "first_name": None,
            "phone_number": "998901234567",
            "photo": None,
            "name": "Ali",
            "description": None,
            "rating": None,
            "default_from_hour": "09:00:00",
            "default_to_hour": "18:00:00",
            "roles": [1]
        },
        {
            "id": 2,
            "telegram_id": 1002,
            "first_name": None,
            "phone_number": "998903241212",
            "photo": None,
            "name": "Karim",
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


# async def all_services():
    return {
        "Strijka": {
            "100.000": {
                "name": "Oddiy strijka",
                "description": "Sochni oddiy qilib qirqish — klassik uslubda."
            },
            "150.000": {
                "name": "Fade strijka",
                "description": "Yuqoridan pastga silliq o‘tuvchi professional qirqim."
            },
            "200.000": {
                "name": "Premium strijka",
                "description": "Professional stilistdan VIP qirqim va styling."
            }
        },
        "Detskaya strijka": {
            "100.000": {
                "name": "Bolalar uchun qirqim",
                "description": "6 yoshgacha bo‘lgan bolalar uchun qulay va xavfsiz qirqim."
            }
        },
        "Family strijka": {
            "150.000": {
                "name": "Oilaviy strijka",
                "description": "2 kishilik oilaviy to‘plam: ota va bola uchun qirqim."
            }
        },
        "Uxod za borodoy": {
            "50.000": {
                "name": "Silliqlash",
                "description": "Soqolni tekislash va chiroyli ko‘rinishga keltirish."
            },
            "70.000": {
                "name": "Soqol dizayni",
                "description": "Soqolga shakl berish va dizayn."
            },
            "90.000": {
                "name": "To‘liq soqol parvarishi",
                "description": "Yuvish, yog‘ bilan parvarish, uslub berish."
            }
        }
    }

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
