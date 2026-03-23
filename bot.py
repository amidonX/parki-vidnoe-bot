import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = os.getenv("TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище заявок пользователя (в памяти)
user_requests = {}  # {user_id: [list of requests]}

class Form(StatesGroup):
    park = State()
    location = State()
    description = State()
    photo = State()

parks = {
    "central": "Центральный парк",
    "aparinki": "Лесопарк Апаринки",
    "rastorguev": "Расторгуевский парк",
    "timohovskiy": "Тимоховский парк",
    "vysota": "Лесопарк Высота"
}

# ==================== ГЛАВНОЕ МЕНЮ ====================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆕 Новый запрос")],
        [KeyboardButton(text="📋 Мои заявки")],
        [KeyboardButton(text="📸 Без фото")],
        [KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Добро пожаловать в сервисный бот Парков города Видное!", reply_markup=main_menu)
    hour = datetime.now().hour
    greeting = "Доброе утро" if 5 <= hour < 12 else "Добрый день" if 12 <= hour < 17 else "Добрый вечер" if 17 <= hour < 23 else "Доброй ночи"
    await message.answer(f"{greeting}!\n\nНажмите «🆕 Новый запрос», чтобы оставить заявку.", reply_markup=main_menu)

# ==================== НОВЫЙ ЗАПРОС ====================
@dp.message(F.text == "🆕 Новый запрос")
async def new_request(message: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Центральный парк", callback_data="central")],
        [InlineKeyboardButton(text="Лесопарк Апаринки", callback_data="aparinki")],
        [InlineKeyboardButton(text="Расторгуевский парк", callback_data="rastorguev")],
        [InlineKeyboardButton(text="Тимоховский парк", callback_data="timohovskiy")],
        [InlineKeyboardButton(text="Лесопарк Высота", callback_data="vysota")]
    ])
    await message.answer("Выберите парк:", reply_markup=kb)

# ==================== МОИ ЗАЯВКИ ====================
@dp.message(F.text == "📋 Мои заявки")
async def my_requests(message: Message):
    user_id = message.from_user.id
    requests = user_requests.get(user_id, [])

    if not requests:
        await message.answer("У вас пока нет заявок.")
        return

    text = "📋 **Ваши последние заявки:**\n\n"
    for i, req in enumerate(requests[-5:], 1):  # последние 5
        date = req['date']
        park = req['park']
        loc = f" | {req['location']}" if req.get('location') else ""
        desc = req['description'][:100] + "..." if len(req['description']) > 100 else req['description']
        text += f"{i}. **{date}** — {park}{loc}\n{desc}\n\n"

    await message.answer(text)

# ==================== ОБРАБОТКА ЗАЯВКИ ====================
# (выбор парка, описание, фото — как раньше, но с сохранением в user_requests)

@dp.callback_query(lambda c: c.data in parks)
async def choose_park(callback: CallbackQuery, state: FSMContext):
    park_name = parks[callback.data]
    await state.update_data(park=park_name)

    if callback.data == "vysota":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="ПЛК 1", callback_data="vysota_plk1")],
            [InlineKeyboardButton(text="Красный камень", callback_data="vysota_krasny")],
            [InlineKeyboardButton(text="Комната матери и ребенка", callback_data="vysota_mother")]
        ])
        await callback.message.answer("Выберите в какой части парка:", reply_markup=kb)
    else:
        await callback.message.answer(f"Вы выбрали: **{park_name}**\n\nКратко опишите проблему:")
        await state.set_state(Form.description)

@dp.callback_query(lambda c: c.data.startswith("vysota_"))
async def vysota_location(callback: CallbackQuery, state: FSMContext):
    loc = {"vysota_plk1": "ПЛК 1", "vysota_krasny": "Красный камень", "vysota_mother": "Комната матери и ребенка"}[callback.data]
    await state.update_data(location=loc)
    await callback.message.answer(f"Вы выбрали: **{loc}**\n\nКратко опишите проблему:")
    await state.set_state(Form.description)

@dp.message(Form.description)
async def get_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Без фото")]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Прикрепите фото или нажмите кнопку ниже:", reply_markup=kb)
    await state.set_state(Form.photo)

@dp.message(Form.photo)
async def get_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    park = data["park"]
    location = data.get("location", "")
    desc = data["description"]
    user_id = message.from_user.id

    # Сохраняем заявку в историю пользователя
    if user_id not in user_requests:
        user_requests[user_id] = []
    
    user_requests[user_id].append({
        "date": datetime.now().strftime("%d.%m %H:%M"),
        "park": park,
        "location": location,
        "description": desc
    })

    # Отправляем в группу
    text = f"🚨 Новая заявка!\n\n🏞 Парк: {park}"
    if location:
        text += f"\n📍 Место: {location}"
    text += f"\n📝 Проблема: {desc}\n👤 От: {message.from_user.full_name}"

    if message.photo:
        await bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=text)
    else:
        await bot.send_message(GROUP_ID, text)

    await message.answer("✅ Спасибо! Ваша заявка отправлена и сохранена в «Мои заявки».\n\nМожете посмотреть её в любое время.", reply_markup=main_menu)
    await state.clear()

# ==================== ОСТАЛЬНЫЕ КНОПКИ ====================
@dp.message(F.text == "📸 Без фото")
async def no_photo(message: Message):
    await message.answer("📸 Режим без фото активирован.\nНажмите «🆕 Новый запрос» и опишите проблему.")

@dp.message(F.text == "❓ Помощь")
async def help_cmd(message: Message):
    await message.answer("🤖 **Помощь**\n\n• 🆕 Новый запрос — оставить заявку\n• 📋 Мои заявки — посмотреть ваши обращения\n• 📸 Без фото — отправить заявку без фотографии")

async def main():
    print("🤖 Бот запущен с функцией «Мои заявки»!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
