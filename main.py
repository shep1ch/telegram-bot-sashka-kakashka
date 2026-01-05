import asyncio
import sqlite3
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
# Вставь свой токен ниже или используй переменную окружения
TOKEN = "8337757802:AAEWts-t_fYml1nXnGdLeZXoXd2rQwjIMzM" 
ADMIN_ID = 5453703533

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def init_db():
    with sqlite3.connect('bot_data.db') as conn:
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)')
        cur.execute('''CREATE TABLE IF NOT EXISTS videos 
                       (id INTEGER PRIMARY KEY AUTOINCREMENT, cat_id INTEGER, title TEXT, file_id TEXT)''')
        conn.commit()

# --- СОСТОЯНИЯ (FSM) ---
class AdminStates(StatesGroup):
    add_category = State()
    video_choice_cat = State()
    video_title = State()
    video_file = State()

# --- ГЛАВНОЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="📁 Посмотреть папки", callback_data="show_categories")
    
    if message.from_user.id == ADMIN_ID:
        builder.button(text="⚙️ Админ-панель", callback_data="admin_panel")
    
    builder.adjust(1)
    await message.answer(f"Добро пожаловать в бота от WestJoint ,здесь вы найдете лучший дом под себя.Выберите формат., {message.from_user.first_name}", reply_markup=builder.as_markup())

# --- АДМИН-ПАНЕЛЬ ---
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Создать папку", callback_data="add_cat")
    builder.button(text="➕ Добавить видео", callback_data="add_vid")
    builder.button(text="❌ Удалить папку", callback_data="del_cat_list")
    builder.button(text="⬅️ Назад", callback_data="start_over")
    builder.adjust(2)
    await callback.message.edit_text("Управление ботом:", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "start_over")
async def back_to_start(callback: types.CallbackQuery):
    await cmd_start(callback.message)

# --- ЛОГИКА ПАПОК (СОЗДАНИЕ) ---
@dp.callback_query(F.data == "add_cat")
async def add_cat_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите название новой папки:")
    await state.set_state(AdminStates.add_category)

@dp.message(AdminStates.add_category)
async def add_cat_finish(message: types.Message, state: FSMContext):
    with sqlite3.connect('bot_data.db') as conn:
        conn.execute("INSERT INTO categories (name) VALUES (?)", (message.text,))
    await message.answer(f"Папка '{message.text}' создана!")
    await state.clear()

# --- ЛОГИКА ВИДЕО (ДОБАВЛЕНИЕ) ---
@dp.callback_query(F.data == "add_vid")
async def add_vid_start(callback: types.CallbackQuery, state: FSMContext):
    with sqlite3.connect('bot_data.db') as conn:
        cats = conn.execute("SELECT * FROM categories").fetchall()
    
    if not cats:
        await callback.answer("Сначала создайте папку!", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for cid, name in cats:
        builder.button(text=name, callback_data=f"setcat_{cid}")
    builder.adjust(2)
    await callback.message.answer("Выберите папку для видео:", reply_markup=builder.as_markup())
    await state.set_state(AdminStates.video_choice_cat)
@dp.callback_query(AdminStates.video_choice_cat, F.data.startswith("setcat_"))
async def add_vid_title(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(cat_id=callback.data.split("_")[1])
    await callback.message.answer("Введите название для видео:")
    await state.set_state(AdminStates.video_title)
    
