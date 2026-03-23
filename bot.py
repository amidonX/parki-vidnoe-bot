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

# Хранилища
user_requests = {}
pending_done = {}   # staff_id → user_id

class Form(StatesGroup):
    park = State()
    location = State()
    description = State()
    photo = State()           # ← ИСПРАВЛЕНО И ДОБАВЛЕНО
    done_comment = State()    # для ответа о выполнении

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

# Новый запрос
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

# Мои заявки
@dp.message(F.text == "📋 Мои заявки")
async def my_requests(message: Message):
    user_id = message.from_user.id
    requests = user_requests.get(user_id, [])
    if not requests:
        await message.answer("У вас пока нет отправленных заявок.")
        return
    text = "📋 **Ваши последние заявки:**\n\n"
    for i, r in enumerate(requests[-5:], 1):
        loc = f" | {r['location']}" if r.get('location') else ""
        text += f"{i}. **{r['date']}** — {r['park']}{loc}\n{r['description'][:80]}...\n\n"
    await message.answer(text)

# Без фото
@dp.message(F.text == "📸 Без фото")
async def no_photo(message: Message):
    await message.answer("📸 Режим без фото активирован.\nНажмите «🆕 Новый запрос».")

# Помощь
@dp.message(F.text == "❓ Помощь")
async def help_cmd(message: Message):
    await message.answer("🤖 **Как пользоваться:**\n\n🆕 Новый запрос — оставить заявку\n📋 Мои заявки — посмотреть ваши обращения\n📸 Без фото — отправить заявку без фото")

# Выбор парка
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

# Уточнение для Высоты
@dp.callback_query(lambda c: c.data.startswith("vysota_"))
async def vysota_location(callback: CallbackQuery, state: FSMContext):
    loc_map = {"vysota_plk1": "ПЛК 1", "vysota_krasny": "Красный камень", "vysota_mother": "Комната матери и ребенка"}
    loc = loc_map[callback.data]
    await state.update_data(location=loc)
    await callback.message.answer(f"Вы выбрали: **{loc}**\n\nКратко опишите проблему:")
    await state.set_state(Form.description)

# Описание проблемы
@dp.message(Form.description)
async def get_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📸 Без фото")]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Прикрепите фото проблемы или нажмите кнопку ниже:", reply_markup=kb)
    await state.set_state(Form.photo)

# Обработка фото / Без фото + отправка заявки
@dp.message(Form.photo)
async def get_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    park = data.get("park", "Неизвестный парк")
    location = data.get("location", "")
    desc = data.get("description", "—")
    user_id = message.from_user.id

    if user_id not in user_requests:
        user_requests[user_id] = []
    user_requests[user_id].append({
        "date": datetime.now().strftime("%d.%m %H:%M"),
        "park": park,
        "location": location,
        "description": desc
    })

    text = f"🚨 Новая заявка!\n\n🏞 Парк: {park}"
    if location:
        text += f"\n📍 Место: {location}"
    text += f"\n📝 Проблема: {desc}\n👤 От: {message.from_user.full_name}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Проблема решена", callback_data=f"done_{user_id}")]
    ])

    if message.photo:
        await bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=text, reply_markup=kb)
    else:
        await bot.send_message(GROUP_ID, text, reply_markup=kb)

    await message.answer("✅ Заявка отправлена!", reply_markup=main_menu)
    await state.clear()

# Закрытие заявки (комментарий + фото результата)
@dp.callback_query(lambda c: c.data.startswith("done_"))
async def problem_done(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[1])
    pending_done[callback.from_user.id] = user_id
    await callback.message.answer("Напишите комментарий о выполнении и/или прикрепите фото результата:")
    await state.set_state(Form.done_comment)

@dp.message(Form.done_comment)
async def get_done_comment(message: Message, state: FSMContext):
    staff_id = message.from_user.id
    user_id = pending_done.get(staff_id)
    if not user_id:
        await message.answer("Ошибка. Попробуйте снова.")
        return

    text = f"✅ **Ваша заявка решена!**\n\n{message.text}\n\nСпасибо, что помогаете нам делать парки лучше! 🌳"

    if message.photo:
        await bot.send_photo(user_id, message.photo[-1].file_id, caption=text)
    else:
        await bot.send_message(user_id, text)

    await message.answer("✅ Уведомление отправлено автору заявки.", reply_markup=main_menu)
    await state.clear()
    pending_done.pop(staff_id, None)

async def main():
    print("🤖 Бот запущен с функцией закрытия заявок + фото результата!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
