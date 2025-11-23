from aiogram import Bot, Dispatcher
from dotenv import load_dotenv, find_dotenv
import os
import asyncio

from src.bot.handlers.user_handlers import user_router
from src.bot.handlers.admin_handlers import admin_router


load_dotenv(find_dotenv())


bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


async def main():
    dp.include_routers(user_router, admin_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot Stoped!")
        
