import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

# Берем токен из настроек сервера (безопасно)
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(F.text)
async def handle_review(message: Message):
    review = message.text
    # Здесь мы создаем 3 варианта ответа
    reply = (
        f"✅ **Вариант 1 (Официальный):**\nБлагодарим за отзыв! Мы рады, что вам понравилось в нашем парке. Ждем вас снова!\n\n"
        f"✅ **Вариант 2 (Теплый):**\nСпасибо большое за добрые слова! Ваша оценка мотивирует нашу команду работать еще лучше.\n\n"
        f"✅ **Вариант 3 (Краткий):**\nРады стараться для жителей Видного! Спасибо, что выбираете наши парки."
    )
    await message.answer(reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
