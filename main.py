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
