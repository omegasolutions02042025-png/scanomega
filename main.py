from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv
import os
from kb import *
from scan_handler import scan_router
from add_info_handler import add_info_router
import asyncio
from teleton_client import client
from google_sheet import update_currency_sheet

load_dotenv()
token = os.getenv('BOT_TOKEN')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
ADMIN_ID = os.getenv('ADMIN_ID')


bot = Bot(token=token)
dp = Dispatcher()





dp.include_router(scan_router)
dp.include_router(add_info_router)


@dp.message(CommandStart())
async def start(message: types.Message):
    if not message.from_user.username:
        await message.reply("Пожалуйста, укажите ваш username в настройках Telegram, чтобы я мог вас идентифицировать.")
        return
    await message.reply("Это бот для анализа резюме к требованиям вакансии.", reply_markup=await start_kb())


async def main():
    #await client.start(phone=PHONE_NUMBER)
    asyncio.create_task(update_currency_sheet())
    await dp.start_polling(bot)

if __name__ == "__main__":
    
    asyncio.run(main())
