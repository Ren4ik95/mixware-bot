import asyncio
import logging
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from core.bot import bot, dp
from db.engine import init_db
from middlewares.subscription import SubscriptionMiddleware
from middlewares.db import DatabaseMiddleware
from handlers import subscription as sub_handler
from handlers import menu, key, mod, my_subscriptions, payment, admin, topup, vpn
from tasks.subscription_checker import run_subscription_checker


def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(sub_handler.router)
    dp.include_router(admin.router)
    dp.include_router(menu.router)
    dp.include_router(key.router)
    dp.include_router(mod.router)
    dp.include_router(my_subscriptions.router)
    dp.include_router(payment.router)
    dp.include_router(topup.router)
    dp.include_router(vpn.router)


def setup_middlewares(dp: Dispatcher) -> None:
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    await init_db()
    setup_middlewares(dp)
    setup_routers(dp)

    asyncio.create_task(run_subscription_checker(bot))

    logging.info("🤖 Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())