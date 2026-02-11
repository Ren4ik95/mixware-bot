from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from core.config import config
from db.engine import AsyncSessionFactory
from db.repository import GateChannelRepo


SUBSCRIPTION_TEXT = (
    "👋 <b>Добро пожаловать!</b>\n\n"
    "Для доступа к боту необходимо подписаться на наши каналы.\n"
    "После подписки нажмите <b>✅ Проверить подписку</b>."
)


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = self._extract_user_id(event)

        if user_id is None:
            return await handler(event, data)

        # Админы проходят без проверки
        if user_id in config.admin_ids:
            return await handler(event, data)

        # Callback проверки подписки — пропускаем в хендлер
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        # Загружаем каналы из БД
        async with AsyncSessionFactory() as session:
            repo = GateChannelRepo(session)
            channels = await repo.get_all()

        if not channels:
            return await handler(event, data)

        bot = data["bot"]

        # Проверяем подписки
        from utils.subscription import check_subscriptions_db
        not_subscribed = await check_subscriptions_db(bot, user_id, channels)

        if not not_subscribed:
            return await handler(event, data)

        from keyboards.subscription import subscription_keyboard_db
        if isinstance(event, Message):
            await event.answer(
                SUBSCRIPTION_TEXT,
                reply_markup=subscription_keyboard_db(not_subscribed)
            )
        elif isinstance(event, CallbackQuery):
            await event.answer("❌ Сначала подпишитесь на каналы!", show_alert=True)
            await event.message.edit_text(
                SUBSCRIPTION_TEXT,
                reply_markup=subscription_keyboard_db(not_subscribed)
            )

    @staticmethod
    def _extract_user_id(event: TelegramObject) -> int | None:
        if isinstance(event, Message):
            return event.from_user.id if event.from_user else None
        if isinstance(event, CallbackQuery):
            return event.from_user.id if event.from_user else None
        return None