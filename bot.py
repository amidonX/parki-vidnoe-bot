import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

TOKEN = os.getenv("TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

# Добавляем default parse_mode, чтобы работал жирный текст (**)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

user_requests = {}

class Form(StatesGroup):
    park = State()
    location = State()
    description = State()
    photo = State()  # ТЕПЕРЬ СОСТОЯНИЕ ЕСТЬ

parks = {
    "central": "Центральный парк",
    "aparinki": "Лесопарк Апаринки",
    "rastorguev": "Расторгуевский парк",
    "timohovskiy": "Тимоховский парк",
    "vysota": "Лесопарк Высота"
}

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆕 Новый запрос")],
        [KeyboardButton(text="📋 Мои заявки")],
        [KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(message: Message):
    hour = datetime.now().hour
    greeting = "Доброе утро" if 5 <= hour < 12 else "Добрый день" if 12 <= hour < 17 else "Добрый вечер" if 17 <= hour < 23 else "Доброй ночи"
    await message.answer(f"{greeting}, {message.from_user.first_name}!\n\nДобро пожаловать в сервисный бот Парков города Видное!\nНажмите «🆕 Новый запрос», чтобы оставить заявку.", reply_markup=main_menu)

@dp.message(F.text == "🆕 Новый запрос")
async def new_request(message: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=v, callback_data=k)] for k, v in parks.items()
    ])
    await message.answer("Выберите парк:", reply_markup=kb)

@dp.message(F.text == "📋 Мои заявки")
async def my_requests(message: Message):
    user_id = message.from_user.id
    requests = user_requests.get(user_id, [])
    if not requests:
        await message.answer("У вас пока нет отправленных заявок.")
        return

    text = "📋 **Ваши последние заявки:**\n\n"
    for i, req in enumerate(requests[-5:], 1):
        date = req['date']
        park = req['park']
        loc = f" ({req['location']})" if req.get('location') else ""
        desc = req['description'][:80] + "..." if len(req['description']) > 80 else req['description']
        text += f"{i}. **{date}** — {park}{loc}\n_{desc}_\n\n"
    await message.answer(text)

# Обработка выбора парка
@dp.callback_query(lambda c: c.data in parks)
async def choose_park(callback: CallbackQuery, state: FSMContext):
    park_name = parks[callback.data]
    await state.update_data(park=park_name)

    if callback.data == "vysota":
        await state.set_state(Form.location) # Устанавливаем состояние перед выбором локации
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="ПЛК 1", callback_data="loc_vysota_plk1")],
            [InlineKeyboardButton(text="Красный камень", callback_data="loc_vysota_krasny")],
            [InlineKeyboardButton(text="Комната матери и ребенка", callback_data="loc_vysota_mother")]
        ])
        await callback.message.edit_text("Выберите часть парка «Высота»:", reply_markup=kb)
    else:
        await state.update_data(location=None)
        await callback.message.answer(f"Вы выбрали: **{park_name}**\n\nКратко опишите проблему:")
        await state.set_state(Form.description)
    await callback.answer()

# Уточнение локации (используем фильтр по префиксу)
@dp.callback_query(F.data.startswith("loc_vysota_"))
async def vysota_location(callback: CallbackQuery, state: FSMContext):
    loc_map = {
        "loc_vysota_plk1": "ПЛК 1", 
        "loc_vysota_krasny": "Красный камень", 
        "loc_vysota_mother": "Комната матери и ребенка"
    }
    loc = loc_map[callback.data]
    await state.update_data(location=loc)
    await callback.message.answer(f"Вы выбрали: **{loc}**\n\nКратко опишите проблему:")
    await state.set_state(Form.description)
    await callback.answer()

@dp.message(Form.description)
async def get_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📸 Без фото")]], 
        resize_keyboard=True, 
        one_time_keyboard=True
    )
    await message.answer("Прикрепите фото проблемы или нажмите кнопку «Без фото»:", reply_markup=kb)
    await state.set_state(Form.photo)

# Финальный этап: фото или текст
@dp.message(Form.photo)
async def get_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    park = data.get("park")
    location = data.get("location")
    desc = data.get("description")

    user_id = message.from_user.id
    if user_id not in user_requests:
        user_requests[user_id] = []

    user_requests[user_id].append({
        "date": datetime.now().strftime("%d.%m %H:%M"),
        "park": park,
        "location": location,
        "description": desc
    })

    text = f"🚨 **Новая заявка!**\n\n🏞 **Парк:** {park}"
    if location:
        text += f"\n📍 **Место:** {location}"
    text += f"\n📝 **Проблема:** {desc}\n👤 **От:** {message.from_user.full_name}"

    try:
        if message.photo:
            await bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=text)
        else:
            await bot.send_message(GROUP_ID, text)
        
        await message.answer("✅ Спасибо! Заявка отправлена администратору.", reply_markup=main_menu)
    except Exception as e:
        await message.answer("❌ Ошибка при отправке в группу. Обратитесь к админу.")
        print(f"Error sending to group: {e}")

    await state.clear()

@dp.message(F.text == "❓ Помощь")
async def help_cmd(message: Message):
    await message.answer("🤖 **Инструкция:**\n\n1. Нажмите «🆕 Новый запрос».\n2. Выберите парк из списка.\n3. Опишите проблему.\n4. Пришлите фото (или нажмите «Без фото»).\n\nВаши заявки сохраняются в разделе «📋 Мои заявки».")

async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
