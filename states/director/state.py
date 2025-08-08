from aiogram.fsm.state import State, StatesGroup

class director(StatesGroup):
    main_menu = State()

    notifications = State()
    input_text = State()
    input_photo = State()
    input_button = State()
    check_post = State()
    confirm_post = State()

    bookings = State()
    today_books = State()
    other_day_books = State()
    cancel_books = State()
    reschedule_books = State()

    settings = State()
    services_prices = State()
    barber_types = State()
    add_type = State()
    delete_type = State()
    barber_services = State()
    service_detail = State()
    add_service = State()
    delete_sevice = State()
    edit_service_name = State()
    edit_service_description = State()
    edit_service_duration = State()
    edit_service_price = State()
    working_hours = State()

    barbers = State()
    add_barber = State()
    add_phone = State()
    add_description = State()
    add_photo = State()
    save_barber = State()
    delete_barber = State()
    delete_barber_confirm_reject = State()

    admins = State()

    clients = State()

    analytics = State()

    finance = State()

    journal = State()

    feedback = State()

    language = State()