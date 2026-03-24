import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    print("✅ Получена команда /start")
    await message.answer("✅ Бот работает! Я тебя вижу.")

@dp.message()
async def echo(message: Message):
    print(f"📨 Получено сообщение: {message.text}")
    await message.answer("✅ Я получил твоё сообщение!")

async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot, drop_pending_updates=True)   # очищаем старые сообщения

if __name__ == "__main__":
    asyncio.run(main())
