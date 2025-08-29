from aiogram.fsm.state import State, StatesGroup

class barber(StatesGroup):
    main_menu = State()

    bookings = State()
    bookings_today = State()
    bookings_otherday = State()

    breaks = State()
    break_add_reason = State()
    break_add_time = State()
    break_add_confirm = State()
    break_edit = State()
    break_edit_time = State()
    break_delete = State()
    break_delete_confirm = State()

    cabinet = State()
    cabinet_phone = State()
    cabinet_about = State()
    cabinet_photo = State()
    cabinet_time = State()
    cabinet_language = State()

    types = State()
    type_add = State()
    type_delete = State()
    type_delete_confirm = State()
    services = State()
    service_add = State()
    service_delete = State()
    service_delete_confirm = State()
    service_detail = State()
    service_name = State()
    service_description = State()
    service_duration = State()
    service_price = State()


class admin(StatesGroup):
    main_menu = State()

    #####################
    notifications = State()

    input_text = State()
    input_photo = State()
    input_button = State()
    check_post = State()
    confirm_post = State()

    #####################
    bookings = State()

    bookings_today = State()
    bookings_barber = State()
    booking_detail = State()
    booking_cancel = State()
    booking_cancel_confirm = State()
    booking_forward = State()
    booking_forward_confirm = State()

    bookings_otherday = State()

    bookings_cancel = State()

    bookings_forward = State()

    #####################
    settings = State()

    services_menu = State()
    barber_types = State()
    type_add = State()
    type_delete = State()
    type_services = State()
    service_detail = State()
    service_add = State()
    service_delete = State()
    service_edit_name = State()
    service_edit_description = State()
    service_edit_duration = State()
    service_edit_price = State()
    
    barbers = State()
    barber_add = State()
    barber_delete = State()
    barber_detail= State()
    barber_edit_phone = State()
    barber_edit_description = State()
    barber_edit_photo = State()
    barber_edit_time = State()

    admins = State()
    admin_add = State()
    admin_delete = State()
    admin_detail = State()
    admin_edit_phone = State()
    admin_edit_button = State()

    working_hours = State()

    language = State()

    #####################
    clients = State()
    client_list = State()
    client_search = State()
    client_detail = State()

    #####################
    analytics = State()

    #####################


class director(StatesGroup):
    main_menu = State()
    
    #####################
    notifications = State()

    input_text = State()
    input_photo = State()
    input_button = State()
    check_post = State()
    confirm_post = State()

    #####################
    bookings = State()

    bookings_today = State()
    bookings_barber = State()
    booking_detail = State()
    booking_cancel = State()
    booking_cancel_confirm = State()
    booking_forward = State()
    booking_forward_confirm = State()

    bookings_otherday = State()

    bookings_cancel = State()

    bookings_forward = State()

    #####################
    settings = State()

    services_menu = State()
    barber_types = State()
    type_add = State()
    type_delete = State()
    type_services = State()
    service_detail = State()
    service_add = State()
    service_delete = State()
    service_edit_name = State()
    service_edit_description = State()
    service_edit_duration = State()
    service_edit_price = State()
    
    barbers = State()
    barber_add = State()
    barber_delete = State()
    barber_detail= State()
    barber_edit_phone = State()
    barber_edit_description = State()
    barber_edit_photo = State()
    barber_edit_time = State()

    admins = State()
    admin_add = State()
    admin_delete = State()
    admin_detail = State()
    admin_edit_phone = State()
    admin_edit_button = State()

    working_hours = State()

    language = State()

    #####################
    clients = State()
    client_list = State()
    client_search = State()
    client_detail = State()

    #####################
    analytics = State()

    #####################