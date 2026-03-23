import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = os.getenv("TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    park = State()
    description = State()
    photo = State()                     # ← ЭТО ДОЛЖНО БЫТЬ!

parks = {
    "central": "Центральный парк",
    "aparinki": "Лесопарк Апаринки",
    "rastorguev": "Расторгуевский парк",
    "timohovskiy": "Тимоховский парк",
    "vysota": "Лесопарк Высота"
}

@dp.message(Command("start"))
async def start(message: Message):
    hour = datetime.now().hour
    greeting = "Доброе утро" if 5 <= hour < 12 else "Добрый день" if 12 <= hour < 17 else "Добрый вечер" if 17 <= hour < 23 else "Доброй ночи"
    
    await message.answer(f"{greeting}!\n\nРады вас приветствовать в сервисном боте Парков города Видное.\n\nЕсли вы обнаружили проблему, пожалуйста, напишите нам.")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Центральный парк", callback_data="central")],
        [InlineKeyboardButton(text="Лесопарк Апаринки", callback_data="aparinki")],
        [InlineKeyboardButton(text="Расторгуевский парк", callback_data="rastorguev")],
        [InlineKeyboardButton(text="Тимоховский парк", callback_data="timohovskiy")],
        [InlineKeyboardButton(text="Лесопарк Высота", callback_data="vysota")]
    ])
    await message.answer("Выберите парк:", reply_markup=kb)

@dp.callback_query(lambda c: c.data in parks)
async def choose_park(callback: CallbackQuery, state: FSMContext):
    park_name = parks[callback.data]
    await state.update_data(park=park_name)
    await callback.message.answer(f"Вы выбрали: **{park_name}**\n\nКратко опишите проблему:")
    await state.set_state(Form.description)

@dp.message(Form.description)
async def get_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Прикрепите фото проблемы (или напишите **«без фото»**):")
    await state.set_state(Form.photo)

@dp.message(Form.photo)
async def get_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    park = data["park"]
    desc = data["description"]

    text = f"🚨 Новая заявка!\n\n🏞 Парк: {park}\n📝 Проблема: {desc}\n👤 От: {message.from_user.full_name}"

    if message.photo:
        await bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=text)
    else:
        await bot.send_message(GROUP_ID, text)

    await message.answer("✅ Спасибо! Информация передана ответственным службам.")
    await state.clear()

@dp.message(Command("getid"))
async def getid(message: Message):
    await message.answer(f"ID этой группы: <code>{message.chat.id}</code>")

async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
