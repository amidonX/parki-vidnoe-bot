import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

TOKEN = os.getenv("TOKEN")
BUSINESS_NAME = "Парки Видное"

if not TOKEN:
    print("❌ ТОКЕН НЕ НАЙДЕН! Добавь его в Variables на Railway")
    exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(F.text)
async def generate(message: Message):
    resp1 = f"Уважаемые гости!\n\nБлагодарим Вас за отзыв о посещении {BUSINESS_NAME}. Для нас очень важно мнение каждого посетителя. Рады, что Вам понравилось, и будем ждать Вас снова.\n\nС уважением,\nАдминистрация {BUSINESS_NAME}"
    resp2 = f"Уважаемые гости!\n\nПриносим извинения за доставленные неудобства. Мы внимательно изучили ситуацию и уже приняли меры. Надеемся, что при следующем посещении {BUSINESS_NAME} Вы останетесь довольны.\n\nС уважением,\nАдминистрация {BUSINESS_NAME}"
    resp3 = f"Уважаемые гости!\n\nБлагодарим Вас за оставленный отзыв о {BUSINESS_NAME}. Ваше мнение помогает нам становиться лучше. По указанному вопросу мы уже работаем.\n\nС уважением,\nАдминистрация {BUSINESS_NAME}"
    
    await message.answer("✅ Отзыв обработан. Вот 3 варианта:")
    await message.answer(f"**Вариант 1**:\n{resp1}")
    await message.answer(f"**Вариант 2**:\n{resp2}")
    await message.answer(f"**Вариант 3**:\n{resp3}")

async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
