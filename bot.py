import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# ================== НАСТРОЙКИ ==================
TOKEN = "ВСТАВЬ_СВОЙ_ТОКЕН_СЮДА"          # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
BUSINESS_NAME = "Парки Видное"
# ===============================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        f"👋 Добро пожаловать!\n\n"
        f"Я — бот для ответов на отзывы в Яндекс Бизнес для **{BUSINESS_NAME}**.\n\n"
        f"Перешлите или напишите текст отзыва — я подготовлю **3 варианта деловых ответов**."
    )

@dp.message(F.text)
async def generate_responses(message: Message):
    review = message.text.strip()
    
    # Вариант 1 — Благодарность (для положительных)
    resp1 = (f"Уважаемые гости!\n\n"
             f"Благодарим Вас за отзыв о посещении {BUSINESS_NAME}. "
             f"Для нас очень важно мнение каждого посетителя. "
             f"Рады, что Вам понравилось, и будем ждать Вас снова.\n\n"
             f"С уважением,\nАдминистрация {BUSINESS_NAME}")

    # Вариант 2 — Работа с негативом (извинение + решение)
    resp2 = (f"Уважаемые гости!\n\n"
             f"Приносим извинения за доставленные неудобства, отмеченные в Вашем отзыве. "
             f"Мы внимательно изучили ситуацию и уже приняли меры для устранения замечаний. "
             f"Надеемся, что при следующем посещении {BUSINESS_NAME} Вы останетесь довольны.\n\n"
             f"С уважением,\nАдминистрация {BUSINESS_NAME}")

    # Вариант 3 — Универсальный (вопрос / нейтральный)
    resp3 = (f"Уважаемые гости!\n\n"
             f"Благодарим Вас за оставленный отзыв о {BUSINESS_NAME}. "
             f"Ваше мнение помогает нам становиться лучше. "
             f"По указанному вопросу мы уже работаем и готовы предоставить дополнительную информацию.\n\n"
             f"С уважением,\nАдминистрация {BUSINESS_NAME}")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Использовать Ответ 1", callback_data="copy1")],
        [InlineKeyboardButton(text="📋 Использовать Ответ 2", callback_data="copy2")],
        [InlineKeyboardButton(text="📋 Использовать Ответ 3", callback_data="copy3")]
    ])

    await message.answer(
        f"✅ Отзыв обработан.\n\n"
        f"**Вариант 1** (благодарность):\n{resp1}\n\n"
        f"**Вариант 2** (решение проблемы):\n{resp2}\n\n"
        f"**Вариант 3** (универсальный):\n{resp3}",
        reply_markup=keyboard
    )

async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
