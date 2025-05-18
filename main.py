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
