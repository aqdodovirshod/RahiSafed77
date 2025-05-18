import asyncio
import logging
import os
from datetime import datetime
import re

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, 
    InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, FSInputFile, Location
)

import database as db

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "7686264055:AAHwg2GPH8VnvJRbSv3Ril1ZERbNgXyQF9k"

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
temp_data = {}
os.makedirs("car_photos", exist_ok=True)

class ChatState(StatesGroup):
    chatting = State()

class Registration(StatesGroup):
    phone_number = State()

class PassengerLocation(StatesGroup):
    waiting_for_location = State()

class DriverRegistration(StatesGroup):
    experience = State()
    car_license = State()
    car_photo = State()
    car_model = State()
    car_year = State()
    car_id = State()
    uploading_car_photo = State()
    
class PostRide(StatesGroup):
    from_location = State()
    from_location_map = State()
    to_location = State()
    to_location_map = State()
    date = State()
    time = State()
    price = State()
    seats = State()
    bags = State()
    confirm = State()
    
class EditRide(StatesGroup):
    poster_id = State()
    field = State()
    from_location = State()
    to_location = State()
    date = State()
    time = State()
    price = State()
    seats = State()
    bags = State()
    confirm = State()
    waiting_for_field = State()
    new_time = State()
    new_price = State()
    new_seats = State()
    new_bags = State()
    
class BookRide(StatesGroup):
    poster_id = State()
    seats = State()
    baggage = State()
    confirm = State()
    
class CancelBooking(StatesGroup):
    order_id = State()
    reason = State()
    
class ChatWithUser(StatesGroup):
    user_id = State()
    poster_id = State()
    message = State()
    
class SendLocation(StatesGroup):
    recipient_id = State()


def get_main_keyboard(is_driver=False):
    keyboard = [
        [KeyboardButton(text="🔍 Ёфтани Нақлиёт")],
        [KeyboardButton(text="📜 Бронҳои Ман")],
        [KeyboardButton(text="📨 Чатҳо"), KeyboardButton(text="🔔 Огоҳиҳо")],
    ]
    
    if is_driver:
        keyboard.append([KeyboardButton(text="🚗 Сафарҳои Ман")])
        keyboard.append([KeyboardButton(text="➕ Эълон Кардани Сафари Нав")])
        
    else:
        keyboard.append([KeyboardButton(text="🚗 Ронанда Шудан")])
        
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_phone_keyboard():
    keyboard = [[KeyboardButton(text="📱 Фиристодани рақами телефон", request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_location_keyboard():
    keyboard = [[KeyboardButton(text="📍 Фиристодани макони ҷойгиршавӣ", request_location=True)]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_skip_location_keyboard():
    keyboard = [
        [KeyboardButton(text="📍 Фиристодани макони ҷойгиршавӣ", request_location=True)],
        [KeyboardButton(text="⏭️ Пропустить")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_poster_inline_keyboard(poster_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ин Сафарро Брон Кардан", callback_data=f"book_{poster_id}")],
            [InlineKeyboardButton(text="🗣️ Бо ронанда гуфтугӯ кардан", callback_data=f"chat_driver_{poster_id}")]
        ]
    )
    return keyboard

def get_confirm_booking_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Тасдиқ Кардан", callback_data="confirm_booking"),
                InlineKeyboardButton(text="❌ Бекор Кардан", callback_data="cancel_booking")
            ]
        ]
    )
    return keyboard

def get_confirm_poster_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Эълон Кардан", callback_data="confirm_poster"),
                InlineKeyboardButton(text="❌ Бекор Кардан", callback_data="cancel_poster")
            ]
        ]
    )
    return keyboard

def get_my_ride_keyboard(poster_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Тағйир додан", callback_data=f"edit_ride_{poster_id}")],
            [InlineKeyboardButton(text="❌ Бекор кардан", callback_data=f"cancel_ride_{poster_id}")],
            [InlineKeyboardButton(text="👥 Рӯйхати мусофирон", callback_data=f"passengers_{poster_id}")]
        ]
    )
    return keyboard

def get_edit_ride_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📍 Макони оғоз", callback_data="edit_from")],
            [InlineKeyboardButton(text="🏁 Макони анҷом", callback_data="edit_to")],
            [InlineKeyboardButton(text="📅 Сана", callback_data="edit_date")],
            [InlineKeyboardButton(text="🕒 Вақт", callback_data="edit_time")],
            [InlineKeyboardButton(text="💰 Нарх", callback_data="edit_price")],
            [InlineKeyboardButton(text="💺 Шумораи ҷойҳо", callback_data="edit_seats")],
            [InlineKeyboardButton(text="🧳 Вазни борҳо", callback_data="edit_bags")],
            [InlineKeyboardButton(text="🔙 Бозгашт", callback_data="back_to_rides")]
        ]
    )
    return keyboard

def get_passenger_keyboard(user_id, poster_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗣️ Паём фиристодан", callback_data=f"message_user_{user_id}_{poster_id}")],
            [InlineKeyboardButton(text="📍 Дархости макони ҷойгиршавӣ", callback_data=f"request_location_{user_id}")]
        ]
    )
    return keyboard

def get_booking_keyboard(order_id, driver_id, poster_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Бекор кардани брон", callback_data=f"cancel_booking_{order_id}")],
            [InlineKeyboardButton(text="🗣️ Бо ронанда гуфтугӯ кардан", callback_data=f"chat_with_driver_{driver_id}_{poster_id}")],
            [InlineKeyboardButton(text="📍 Фиристодани макони ҷойгиршавӣ", callback_data=f"send_location_{driver_id}")]
        ]
    )
    return keyboard

def get_back_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Бозгашт", callback_data="back_to_main")]
        ]
    )
    return keyboard

@dp.message(F.text == "📨 Чатҳо")
async def show_chats(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Лутфан сабти ном шавед.")
        return

    conn = db.create_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT poster_id, 
                        CASE 
                            WHEN sender_id = ? THEN receiver_id 
                            ELSE sender_id 
                        END as chat_with
        FROM messages
        WHERE sender_id = ? OR receiver_id = ?
    """, (user['id'], user['id'], user['id']))

    chats = cursor.fetchall()
    conn.close()

    if not chats:
        await message.answer("📭 Шумо ҳоло ягон чат надоред.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[]) 

    for chat in chats:
        partner = db.get_user_by_id(chat['chat_with'])
        if not partner:
            continue
        text = f"💬 Бо {partner['first_name']}"
        callback = f"chat_{chat['poster_id']}_{partner['id']}" 
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    await message.answer("📨 Чатҳои шумо:", reply_markup=keyboard)



@dp.message(F.text == "🔔 Огоҳиҳо")
async def show_notifications(message: Message):
    db_user = db.get_user(message.from_user.id)
    if not db_user:
        await message.answer("Лутфан аввал сабти ном шавед.")
        return

    notifications = db.get_user_notifications(db_user['id'])

    if notifications:
        text = "🔔 Огоҳиҳои охирин:\n\n"
        for note in notifications:
            status = "✅" if note['is_read'] else "🔴"
            created = note['created_at'].split()[0] if note['created_at'] else ""
            text += f"{status} {note['message']} ({created})\n"
        await message.answer(text)
    else:
        await message.answer("📭 Шумо ҳоло огоҳӣ надоред.")



def format_datetime(dt_str):
    time_obj = datetime.fromisoformat(dt_str)
    return time_obj.strftime("%d %b %Y, %H:%M")

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle the /start command"""
    user = db.get_user(message.from_user.id)
    
    if not user:
        user_id = db.create_user(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        await message.answer(
            f"Салом, {message.from_user.first_name}! Хуш омадед ба боти саёҳат.\n"
            f"Барои идома додан, лутфан рақами телефони худро пешниҳод кунед.",
            reply_markup=get_phone_keyboard()
        )
        await state.set_state(Registration.phone_number)
    else:
        driver = db.get_driver_by_user_id(user['id'])
        is_driver = driver is not None
        
        await message.answer(
            f"Салом, {user['first_name']}! Шумо чӣ кор кардан мехоҳед?",
            reply_markup=get_main_keyboard(is_driver)
        )

@dp.message(Registration.phone_number)
async def process_phone(message: Message, state: FSMContext):
    """Process the phone number from the user"""
    if message.contact and message.contact.phone_number:
        db.update_user_phone(message.from_user.id, message.contact.phone_number)
        
        await state.clear()
        await message.answer(
            "Раҳмат! Шумо бомуваффақият ба қайд гирифта шудед.",
            reply_markup=get_main_keyboard(is_driver=False)
        )
    else:
        await message.answer(
            "Лутфан, тугмаи «Фиристодани рақами телефон»-ро пахш кунед.",
            reply_markup=get_phone_keyboard()
        )

@dp.message(F.text == "🚗 Ронанда Шудан")
async def become_driver(message: Message, state: FSMContext):
    """Handle driver registration initiation"""
    user = db.get_user(message.from_user.id)
    
    if not user:
        await message.answer(
            "Лутфан, аввал ба қайд гиред. Барои оғоз /start -ро пахш кунед."
        )
        return
    
    driver = db.get_driver_by_user_id(user['id'])
    if driver:
        await message.answer(
            "Шумо аллакай ҳамчун ронанда ба қайд гирифта шудаед!",
            reply_markup=get_main_keyboard(is_driver=True)
        )
        return
    
    await message.answer(
        "Барои ба қайд гирифтан ҳамчун ронанда, лутфан чанд соли таҷрибаи ронандагӣ доред?",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(DriverRegistration.experience)

@dp.message(DriverRegistration.experience)
async def process_experience(message: Message, state: FSMContext):
    """Process driver experience"""
    try:
        experience = int(message.text)
        if experience < 0:
            raise ValueError("Experience cannot be negative")
            
        await state.update_data(experience=experience)
        await message.answer("Лутфан рақами қайди мошинатонро ворид кунед:")
        await state.set_state(DriverRegistration.car_license)
    except ValueError:
        await message.answer("Лутфан рақами дурустро ворид кунед:")

@dp.message(DriverRegistration.car_license)
async def process_car_license(message: Message, state: FSMContext):
    """Process car license"""
    await state.update_data(car_license=message.text)
    await message.answer("Лутфан модели мошинатонро ворид кунед:")
    await state.set_state(DriverRegistration.car_model)

@dp.message(DriverRegistration.car_model)
async def process_car_model(message: Message, state: FSMContext):
    """Process car model"""
    await state.update_data(car_model=message.text)
    await message.answer("Лутфан соли истеҳсоли мошинатонро ворид кунед:")
    await state.set_state(DriverRegistration.car_year)

@dp.message(DriverRegistration.car_year)
async def process_car_year(message: Message, state: FSMContext):
    """Process car year"""
    try:
        car_year = int(message.text)
        current_year = datetime.now().year
        
        if car_year < 1900 or car_year > current_year:
            raise ValueError("Invalid year")
            
        await state.update_data(car_year=car_year)
        await message.answer("Лутфан рақами шиносномаи мошинро ворид кунед:")
        await state.set_state(DriverRegistration.car_id)
    except ValueError:
        await message.answer(f"Лутфан соли дурустро ворид кунед (1900-{datetime.now().year}):")

@dp.message(DriverRegistration.car_id)
async def process_car_id(message: Message, state: FSMContext):
    """Process car ID"""
    await state.update_data(car_id=message.text)
    await message.answer("Лутфан акси мошинатонро фиристед:")
    await state.set_state(DriverRegistration.car_photo)

@dp.message(DriverRegistration.car_photo)
async def process_car_photo(message: Message, state: FSMContext):
    """Process car photo"""
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Хатогӣ рӯй дод. Лутфан /start-ро пахш кунед.")
        await state.clear()
        return
    
    if not message.photo:
        await message.answer("Лутфан, акси мошинро фиристед.")
        return
    
    photo = message.photo[-1]
    photo_path = f"car_photos/car_{user['id']}_{message.from_user.id}.jpg"
    
    await bot.download(photo, destination=photo_path)
    
    data = await state.get_data()
    
    driver_id = db.register_driver(
        user['id'],
        data['experience'],
        data['car_license'],
        data['car_model'],
        data['car_year'],
        data['car_id'],
        photo_path
    )
    
    await state.clear()
    await message.answer(
        "Табрик! Шумо ҳамчун ронанда бомуваффақият ба қайд гирифта шудед.\n"
        "Акнун шумо метавонед сафарҳо эълон кунед ва мусофиронро қабул кунед.",
        reply_markup=get_main_keyboard(is_driver=True)
    )

@dp.message(F.text == "➕ Эълон Кардани Сафари Нав")
async def post_new_ride(message: Message, state: FSMContext):
    """Handler for posting a new ride"""
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Лутфан, аввал ба қайд гиред. Барои оғоз /start-ро пахш кунед.")
        return
    
    driver = db.get_driver_by_user_id(user['id'])
    if not driver:
        await message.answer(
            "Барои эълон кардани сафар, шумо бояд аввал ҳамчун ронанда ба қайд гирифта шавед.",
            reply_markup=get_main_keyboard(is_driver=False)
        )
        return
    
    await message.answer(
        "Аз куҷо сафарро оғоз мекунед? (шаҳр ё ҷойро ворид кунед)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(PostRide.from_location)

@dp.message(PostRide.from_location)
async def process_from_location(message: Message, state: FSMContext):
    """Process departure location"""
    await state.update_data(from_location=message.text)
    await message.answer(
        "Лутфан макони дақиқи оғози сафарро дар харита нишон диҳед (ихтиёрӣ):",
        reply_markup=get_skip_location_keyboard()
    )
    await state.set_state(PostRide.from_location_map)

@dp.message(PostRide.from_location_map)
async def process_from_location_map(message: Message, state: FSMContext):
    """Process departure location map coordinates"""
    if message.text == "⏭️ Пропустить":
        await state.update_data(from_latitude=None, from_longitude=None)
        await message.answer("Ба куҷо сафар мекунед? (шаҳр ё ҷойро ворид кунед)")
        await state.set_state(PostRide.to_location)
        return
    
    if not message.location:
        await message.answer(
            "Лутфан локатсияро бо тугмаи зерин фиристед ё 'Пропустить'-ро пахш кунед:",
            reply_markup=get_skip_location_keyboard()
        )
        return
    
    await state.update_data(
        from_latitude=message.location.latitude,
        from_longitude=message.location.longitude
    )
    
    await message.answer("Ба куҷо сафар мекунед? (шаҳр ё ҷойро ворид кунед)")
    await state.set_state(PostRide.to_location)

@dp.message(PostRide.to_location)
async def process_to_location(message: Message, state: FSMContext):
    """Process destination location"""
    await state.update_data(to_location=message.text)
    await message.answer(
        "Лутфан макони дақиқи анҷоми сафарро дар харита нишон диҳед (ихтиёрӣ):",
        reply_markup=get_skip_location_keyboard()
    )
    await state.set_state(PostRide.to_location_map)

@dp.message(PostRide.to_location_map)
async def process_to_location_map(message: Message, state: FSMContext):
    """Process destination location map coordinates"""
    if message.text == "⏭️ Пропустить":
        await state.update_data(to_latitude=None, to_longitude=None)
        await message.answer(
            "Санаи сафарро ворид кунед (дар формати ДД.ММ.СССС, масалан 25.05.2025):"
        )
        await state.set_state(PostRide.date)
        return
    
    if not message.location:
        await message.answer(
            "Лутфан локатсияро бо тугмаи зерин фиристед ё 'Пропустить'-ро пахш кунед:",
            reply_markup=get_skip_location_keyboard()
        )
        return
    
    await state.update_data(
        to_latitude=message.location.latitude,
        to_longitude=message.location.longitude
    )
    
    await message.answer(
        "Санаи сафарро ворид кунед (дар формати ДД.ММ.СССС, масалан 25.05.2025):"
    )
    await state.set_state(PostRide.date)

@dp.message(PostRide.date)
async def process_date(message: Message, state: FSMContext):
    """Process ride date"""
    date_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if not re.match(date_pattern, message.text):
        await message.answer(
            "Формати сана нодуруст аст. Лутфан дар шакли ДД.ММ.СССС ворид кунед, масалан 25.05.2025:"
        )
        return
    
    try:
        day, month, year = map(int, message.text.split('.'))
        if not (1 <= day <= 31 and 1 <= month <= 12 and 2023 <= year <= 2030):
            raise ValueError("Invalid date range")
            
        await state.update_data(ride_date=message.text)
        await message.answer(
            "Вақти сафарро ворид кунед (дар формати СС:ДД, масалан 09:30):"
        )
        await state.set_state(PostRide.time)
    except ValueError:
        await message.answer(
            "Санаи нодуруст. Лутфан санаи дурустро ворид кунед:"
        )

@dp.message(PostRide.time)
async def process_time(message: Message, state: FSMContext):
    """Process ride time"""
    time_pattern = r"^\d{1,2}:\d{2}$"
    if not re.match(time_pattern, message.text):
        await message.answer(
            "Формати вақт нодуруст аст. Лутфан дар шакли СС:ДД ворид кунед, масалан 09:30:"
        )
        return
    
    try:
        hours, minutes = map(int, message.text.split(':'))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError("Invalid time")
            
        await state.update_data(ride_time=message.text)
        
        await message.answer("Нархи сафарро ба сомонӣ ворид кунед:")
        await state.set_state(PostRide.price)
    except ValueError:
        await message.answer("Вақти нодуруст. Лутфан вақти дурустро ворид кунед:")

@dp.message(PostRide.price)
async def process_price(message: Message, state: FSMContext):
    """Process ride price"""
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError("Price must be positive")
            
        await state.update_data(price=price)
        await message.answer("Шумораи ҷойҳои озодро ворид кунед:")
        await state.set_state(PostRide.seats)
    except ValueError:
        await message.answer("Лутфан нархи дуруст ворид кунед (рақам):")

@dp.message(PostRide.seats)
async def process_seats(message: Message, state: FSMContext):
    """Process available seats"""
    try:
        seats = int(message.text)
        if seats <= 0:
            raise ValueError("Seats must be positive")
            
        await state.update_data(seats=seats)
        await message.answer("Шумораи максималии ҷойҳо барои борҳоро ворид кунед:")
        await state.set_state(PostRide.bags)
    except ValueError:
        await message.answer("Лутфан шумораи дурусти ҷойҳоро ворид кунед (рақами бутун):")

@dp.message(PostRide.bags)
async def process_bags(message: Message, state: FSMContext):
    """Process baggage capacity"""
    try:
        bags = int(message.text)
        if bags < 0:
            raise ValueError("Baggage count cannot be negative")
            
        await state.update_data(bags=bags)
        
        data = await state.get_data()
        
        date_str = data['ride_date']
        time_str = data['ride_time']
        day, month, year = map(int, date_str.split('.'))
        hour, minute = map(int, time_str.split(':'))
        
        confirmation_text = (
            "Лутфан маълумотро тасдиқ кунед:\n\n"
            f"🚏 Аз: {data['from_location']}\n"
            f"🏁 Ба: {data['to_location']}\n"
            f"🕒 Вақт: {date_str} {time_str}\n"
            f"💰 Нарх: {data['price']} сомонӣ\n"
            f"💺 Ҷойҳои холӣ: {data['seats']}\n"
            f"🧳 Вазни бор (як кас): {data['bags']}"
        )
        
        await message.answer(confirmation_text, reply_markup=get_confirm_poster_keyboard())
        await state.set_state(PostRide.confirm)
    except ValueError:
        await message.answer("Лутфан шумораи дурусти борҳоро ворид кунед (рақами бутун):")

@dp.callback_query(PostRide.confirm, F.data == "confirm_poster")
async def confirm_poster(callback: CallbackQuery, state: FSMContext):
    """Handle poster confirmation"""
    user = db.get_user(callback.from_user.id)
    if not user:
        await callback.message.answer("Хатогӣ рӯй дод. Лутфан /start-ро пахш кунед.")
        await callback.answer()
        await state.clear()
        return
    
    driver = db.get_driver_by_user_id(user['id'])
    if not driver:
        await callback.message.answer("Шумо бояд аввал ҳамчун ронанда ба қайд гирифта шавед.")
        await callback.answer()
        await state.clear()
        return
    
    data = await state.get_data()
    
    date_str = data['ride_date']
    time_str = data['ride_time']
    day, month, year = map(int, date_str.split('.'))
    hour, minute = map(int, time_str.split(':'))
    
    time_to_go = datetime(year, month, day, hour, minute).isoformat()
    
    poster_id = db.create_poster(
        driver_id=driver['id'],
        from_location=data['from_location'],
        to_location=data['to_location'],
        price=data['price'],
        seat_count=data['seats'],
        time_to_go=time_to_go,
        bags_count=data['bags'],
        from_latitude=data.get('from_latitude'),
        from_longitude=data.get('from_longitude'),
        to_latitude=data.get('to_latitude'),
        to_longitude=data.get('to_longitude')
    )
    
    await callback.message.edit_text(
        "✅ Сафари шумо бомуваффақият эълон карда шуд!\n\n"
        "Шумо метавонед онро дар қисмати «Сафарҳои Ман» бинед."
    )
    
    await callback.answer("Сафар бомуваффақият эълон карда шуд!")
    await state.clear()
    
    await callback.message.answer(
        "Шумо чӣ кор кардан мехоҳед?",
        reply_markup=get_main_keyboard(is_driver=True)
    )

@dp.callback_query(PostRide.confirm, F.data == "cancel_poster")
async def cancel_poster_creation(callback: CallbackQuery, state: FSMContext):
    """Handle poster cancellation"""
    await callback.message.edit_text("❌ Эълони сафар бекор карда шуд.")
    await callback.answer("Эълони сафар бекор карда шуд")
    await state.clear()
    
    user = db.get_user(callback.from_user.id)
    is_driver = False
    if user:
        driver = db.get_driver_by_user_id(user['id'])
        is_driver = driver is not None
    
    await callback.message.answer(
        "Шумо чӣ кор кардан мехоҳед?",
        reply_markup=get_main_keyboard(is_driver=is_driver)
    )

@dp.message(F.text == "🔍 Ёфтани Нақлиёт")
async def find_rides(message: Message):
    """Display available rides"""
    posters = db.get_active_posters()
    
    if not posters:
        await message.answer(
            "Айни ҳол ягон сафари фаъол мавҷуд нест.\n"
            "Лутфан дертар бинед ё огоҳиҳо гиред вақте ки сафари нав пайдо мешавад."
        )
        return
    
    for poster in posters:
        ride_time = format_datetime(poster['time_to_go'])
        
        driver_name = f"{poster['first_name']} {poster['last_name'] or ''}"
        
        car_photo = poster.get('car_photo')
        
        message_text = (
            f"🚗 Сафар аз {poster['from_location']} то {poster['to_location']}\n"
            f"🕒 Вақт: {ride_time}\n"
            f"💰 Нарх: {poster['price']} сомонӣ\n"
            f"💺 Ҷойҳои холӣ: {poster['seat_count']}\n"
            f"🧳 Вазни бор (як кас): {poster['bags_count']}\n"
            f"👨‍✈️ Ронанда: {driver_name}\n"
            f"🚘 Мошин: {poster['car_model']}"
        )
        
        if car_photo and os.path.exists(car_photo):
            await message.answer_photo(
                FSInputFile(car_photo),
                caption=message_text,
                reply_markup=get_poster_inline_keyboard(poster['id'])
            )
        else:
            await message.answer(
                message_text,
                reply_markup=get_poster_inline_keyboard(poster['id'])
            )

@dp.message(F.text == "🚗 Сафарҳои Ман")
async def my_rides(message: Message):
    """Display driver's rides"""
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Лутфан, аввал ба қайд гиред. Барои оғоз /start-ро пахш кунед.")
        return
    
    driver = db.get_driver_by_user_id(user['id'])
    if not driver:
        await message.answer(
            "Шумо ҳанӯз ҳамчун ронанда ба қайд гирифта нашудаед.",
            reply_markup=get_main_keyboard(is_driver=False)
        )
        return
    
    posters = db.get_driver_posters(driver['id'])
    
    if not posters:
        await message.answer(
            "Шумо ҳанӯз ягон сафар эълон накардаед.\n"
            "Барои эълон кардани сафари нав, тугмаи «Эълон Кардани Сафари Нав»-ро пахш кунед."
        )
        return
    
    for poster in posters:
        ride_time = format_datetime(poster['time_to_go'])
        
        status = "🟢 Фаъол" if poster['is_active'] else "🔴 Ғайри фаъол"
        orders = f"👥 Бронҳо: {poster['order_count']}"
        
        message_text = (
            f"🚗 Сафар аз {poster['from_location']} то {poster['to_location']}\n"
            f"🕒 Вақт: {ride_time}\n"
            f"💰 Нарх: {poster['price']} сомонӣ\n"
            f"💺 Ҷойҳои холӣ: {poster['seat_count']}\n"
            f"🧳 Вазни бор (як кас): {poster['bags_count']}\n"
            f"{status} • {orders}"
        )
        
        await message.answer(
            message_text,
            reply_markup=get_my_ride_keyboard(poster['id'])
        )


@dp.callback_query(F.data.startswith("book_")) 
async def book_ride(callback: CallbackQuery, state: FSMContext):
    """Handle ride booking"""
    poster_id = int(callback.data.split("_")[1])
    
    poster = db.get_poster_by_id(poster_id)
    if not poster or not poster['is_active']:
        await callback.message.answer("Ин сафар дигар дастрас нест.")
        await callback.answer("Сафар дастрас нест")
        return
    
    await state.update_data(poster_id=poster_id)
    
    await callback.message.answer(
        f"Шумо сафарро интихоб кардед аз {poster['from_location']} то {poster['to_location']}.\n"
        f"Чанд ҷой брон мекунед? (максимум {poster['seat_count']} ҷой):"
    )
    
    await state.set_state(BookRide.seats)
    await callback.answer()

@dp.message(BookRide.seats)
async def process_booking_seats(message: Message, state: FSMContext):
    """Process booking seats"""
    try:
        seats = int(message.text)
        data = await state.get_data()
        poster_id = data['poster_id']
        
        poster = db.get_poster_by_id(poster_id)
        if not poster or not poster['is_active']:
            await message.answer("Ин сафар дигар дастрас нест.")
            await state.clear()
            return
        
        if seats <= 0:
            await message.answer("Лутфан шумораи мусбати ҷойҳоро ворид кунед.")
            return
            
        if seats > poster['seat_count']:
            await message.answer(
                f"Дар сафар танҳо {poster['seat_count']} ҷой мавҷуд аст.\n"
                f"Лутфан камтар ҷой интихоб кунед:"
            )
            return
        
        await state.update_data(seats=seats)
        
        if poster['bags_count'] > 0:
            await message.answer(
                f"Вазни тахминии бағоҷи худро бо килограмм ворид кунед (0 агар бағоҷ надоред):"
            )
            await state.set_state(BookRide.baggage)
        else:
            await state.update_data(baggage=0)
            
            ride_time = format_datetime(poster['time_to_go'])
            
            await message.answer(
                "Лутфан брони худро тасдиқ кунед:\n\n"
                f"🚏 Аз: {poster['from_location']}\n"
                f"🏁 Ба: {poster['to_location']}\n"
                f"🕒 Вақт: {ride_time}\n"
                f"💰 Нарх: {poster['price'] * seats} сомонӣ ({poster['price']} × {seats})\n"
                f"💺 Ҷойҳо: {seats}\n"
                f"🧳 Бор: Не\n"
                f"👨‍✈️ Ронанда: {poster['first_name']} {poster['last_name'] or ''}",
                reply_markup=get_confirm_booking_keyboard()
            )
            
            await state.set_state(BookRide.confirm)
            
    except ValueError:
        await message.answer("Лутфан рақами дурустро ворид кунед:")

@dp.message(BookRide.baggage)
async def process_baggage(message: Message, state: FSMContext):
    """Process baggage information"""
    try:
        baggage = int(message.text)
        if baggage < 0:
            await message.answer("Лутфан рақами мусбатро ворид кунед:")
            return
        
        data = await state.get_data()
        poster_id = data['poster_id']
        seats = data['seats']
        
        poster = db.get_poster_by_id(poster_id)
        if not poster:
            await message.answer("Ин сафар дигар дастрас нест.")
            await state.clear()
            return
        
        await state.update_data(baggage=baggage)
        
        ride_time = format_datetime(poster['time_to_go'])
        
        await message.answer(
            "Лутфан брони худро тасдиқ кунед:\n\n"
            f"🚏 Аз: {poster['from_location']}\n"
            f"🏁 Ба: {poster['to_location']}\n"
            f"🕒 Вақт: {ride_time}\n"
            f"💰 Нарх: {poster['price'] * seats} сомонӣ ({poster['price']} × {seats})\n"
            f"💺 Ҷойҳо: {seats}\n"
            f"🧳 Бор: {baggage} кг\n"
            f"👨‍✈️ Ронанда: {poster['first_name']} {poster['last_name'] or ''}",
            reply_markup=get_confirm_booking_keyboard()
        )
        
        await state.set_state(BookRide.confirm)
    except ValueError:
        await message.answer("Лутфан рақами дурустро ворид кунед:")

@dp.callback_query(F.data == "confirm_booking", BookRide.confirm)
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    """Confirm booking"""
    user_id = callback.from_user.id
    db_user = db.get_user(user_id)
    
    if not db_user:
        await callback.message.answer("Лутфан аввал бақайдгирӣ гузаред.")
        await callback.answer()
        return
    
    data = await state.get_data()
    poster_id = data['poster_id']
    seats = data['seats']
    baggage = data.get('baggage', 0)
    
    try:
        order_id = db.create_order(poster_id, db_user['id'], seats, baggage)
        
        poster = db.get_poster_by_id(poster_id)
        
        await callback.message.answer(
            "✅ Брони шумо тасдиқ карда шуд!\n\n"
            f"🔢 Рақами брон: #{order_id}\n"
            f"🚏 Аз: {poster['from_location']}\n"
            f"🏁 Ба: {poster['to_location']}\n"
            f"🕒 Вақт: {format_datetime(poster['time_to_go'])}\n"
            f"💰 Нарх: {poster['price'] * seats} сомонӣ\n"
            f"💺 Ҷойҳо: {seats}\n"
            f"🧳 Бор: {baggage} кг\n\n"
            f"👨‍✈️ Ронанда: {poster['first_name']} {poster['last_name'] or ''}\n"
            f"📞 Телефон: {poster['phone_number']}\n\n"
            "Шумо метавонед бо истифода аз менюи асосӣ брони худро дида бароед ва бо ронанда тамос гиред.",
            reply_markup=get_main_keyboard()
        )
        
        driver_telegram_id = None
        try:
            driver_user = db.get_user_by_id(poster['user_id'])
            if driver_user:
                driver_telegram_id = driver_user['telegram_id']
                
                if driver_telegram_id:
                    await bot.send_message(
                        driver_telegram_id,
                        f"🆕 Брони нав барои сафари шумо:\n\n"
                        f"🚏 Аз: {poster['from_location']}\n"
                        f"🏁 Ба: {poster['to_location']}\n"
                        f"🕒 Вақт: {format_datetime(poster['time_to_go'])}\n"
                        f"👤 Мусофир: {callback.from_user.full_name}\n"
                        f"💺 Ҷойҳо: {seats}\n"
                        f"🧳 Бор: {baggage} кг\n\n"
                        "Барои дидани маълумоти пурра, ба 'Сафарҳои ман' ворид шавед."
                    )
        except Exception as e:
            logging.error(f"Error notifying driver: {e}")
        
        await state.clear()
    except Exception as e:
        logging.error(f"Error creating order: {e}")
        await callback.message.answer("Хатогӣ ҳангоми брон. Лутфан боз кӯшиш кунед.")
    
    await callback.answer()

@dp.callback_query(F.data == "cancel_booking", BookRide.confirm)
async def cancel_booking_process(callback: CallbackQuery, state: FSMContext):
    """Cancel booking process"""
    await callback.message.answer("Брон бекор карда шуд.", reply_markup=get_main_keyboard())
    await state.clear()
    await callback.answer()