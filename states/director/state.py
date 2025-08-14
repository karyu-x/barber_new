from aiogram.fsm.state import State, StatesGroup

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

    today_books = State()
    barber_books = State()

    other_day_books = State()

    cancel_books = State()

    reschedule_books = State()

    #####################
    settings = State()

    services_prices = State()
    barber_types = State()
    add_type = State()
    delete_type = State()
    barber_services = State()
    service_detail = State()
    add_service = State()
    delete_service = State()
    edit_service_name = State()
    edit_service_description = State()
    edit_service_duration = State()
    edit_service_price = State()
    
    barbers = State()
    barber_detail= State()
    edit_barber_phone = State()
    edit_barber_description = State()
    edit_barber_photo = State()
    edit_barber_time = State()
    add_barber = State()
    add_phone = State()
    add_description = State()
    add_photo = State()
    delete_barber = State()

    admins = State()
    admin_detail = State()
    add_admin = State()
    edit_admin_phone = State()
    edit_admin_button = State()
    delete_admin = State()

    working_hours = State()

    #####################
    clients = State()

    #####################
    analytics = State()

    #####################
    finance = State()

    #####################
    journal = State()

    #####################
    feedback = State()

    #####################
    language = State()