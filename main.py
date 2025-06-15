import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TELEGRAM_TOKEN
from handlers import user, admin, proof

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(proof.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())