from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from db.engine import AsyncSessionFactory
from db.repository import UserRepo, SubscriptionRepo, PaymentRepo, GateChannelRepo, ModChannelRepo


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with AsyncSessionFactory() as session:
            data["session"] = session
            data["user_repo"] = UserRepo(session)
            data["sub_repo"] = SubscriptionRepo(session)
            data["pay_repo"] = PaymentRepo(session)
            data["gate_repo"] = GateChannelRepo(session)
            data["mod_repo"] = ModChannelRepo(session)
            return await handler(event, data)