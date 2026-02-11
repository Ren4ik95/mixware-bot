from aiogram import Router
from aiogram.types import Message
from db.repository import UserRepo, SubscriptionRepo
from core.config import config

router = Router()

NO_SUB_TEXT = (
    "🔒 <b>Доступ ограничен</b>\n\n"
    "Для получения ключа необходима активная подписка.\n"
    "Нажмите <b>🛒 Купить подписку</b> для оформления."
)


async def send_key(message: Message, user_repo: UserRepo, sub_repo: SubscriptionRepo) -> None:
    from core.config import config
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    is_admin = message.from_user.id in config.admin_ids
    active_sub = await sub_repo.get_active(user.id) if user else None

    if not active_sub and not is_admin:
        await message.answer(NO_SUB_TEXT)
        return

    await message.answer(
        f"🔑 <b>Ваш ключ активации:</b>\n\n"
        f"<code>{config.license_key}</code>\n\n"
        f"⚠️ Не передавайте ключ третьим лицам."
    )