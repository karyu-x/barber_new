#### SERVICE ####

GET_barber_types = [
    {
        "id": 1,                # TYPE ID   
        "name": "Strijka",      # TYPE NAME
        "barbaer": 123456789    # BARBER TG_ID
    }
]

POST_barber_type_add = {
    "name": "Strijka",      # TYPE NAME
    "barber": 123456789,    # BARBER TG_ID
}

GET_barber_services = [
    {
        "id": 1,                                        # SERVICE ID
        "name": "Fade strijka",                         # SERVICE NAME
        "description": "Fade strijka haqida ma'lumot",  # SERVICE DESCRIPTION
        "duration": "30 minut",                         # SERVICE DURATION
        "price": 100.000,                               # SERVICE PRICE
        "service_type": 1                               # TYPE ID
    }
]

GET_barber_service_with_id = {
    "id": 1,                                        # SERVICE ID
    "name": "Fade strijka",                         # SERVICE NAME
    "description": "Fade strijka haqida ma'lumot",  # SERVICE DESCRIPTION
    "duration": "30 minut",                         # SERVICE DURATION
    "price": 100.000,                               # SERVICE PRICE
    "service_type": 1                               # TYPE ID
}

POST_barber_service_add = {
    "name": "Fade strijka",                         # SERVICE NAME
    "description": "Fade strijka haqida ma'lumot",  # SERVICE DESCRIPTION
    "duration": "30 minut",                         # SERVICE DURATION
    "price": 100.000,                               # SERVICE PRICE
    "service_type": 1                               # TYPE ID
}

GET_barbers_all = [
    {
        "id": 1,
        "tg_id": 123456789,
        "name": "Ali",
        "description": "Ali haqida ma'lumot",
        "photo": photo_id,
        "rating": 4.5,
    }
]
































# RASSILKA UCHUN
userlar_tg = {
    "tg_id": []
}

# BRONLAR
barberla_nomi = {
    "ismlar": {
        "tg_id": ""
    }
}

# BARBERNI BRON QILINGAN VAQTLARI
bron_times = {
    "barber": "tg_id"
}

# Ali -> 9.00 | 10:00

tanlangan_bron = {
    "date": {
        "barber_name": "",
        "bron_time": "",
        "tg_id_client": {
            "name": "",
            "phone": ""
        },
        "service": {
            "name": "",
            "price": ""
        },
        "payment": "click/naqt"
    }
}

# tanlanmagan_vaqtlar = {
#     "barber_name": {
#         "times": []
#     }
# }

# BRON KUNLAR 
bron_boshqa_kunlar = {
    "kunlar": []
}

# XIMATDAGI BARBER NOMI

xizmat_barber = {
    "barber_tg_id": {
        "name": "",
    }
}

barber_service = {
    "barber_tg_id": {
        "type_name": {
            "name": {
                "desc": "",
                "price": ""
            }
        }
    }
}

# BARBER HAQIDA
barber = {
    "id": {
        "decrip": "",
        "photo": "",
        "name": "",
        "rating": "",
        "service": {
            "type_name": {
                "name": {
                    "desc": "",
                    "price": ""
                }
            }
        },
        "free_times": {
            "bugun": [],
            "boshqa_kunlar": {
                "sana": {
                    "soatlar": []
                }
            }
        }
    }
}



# KNOPKALAR

knopkalar = {
    "user_id": []
}