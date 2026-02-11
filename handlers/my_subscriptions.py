from aiogram import Router
from aiogram.types import Message
from db.repository import UserRepo, SubscriptionRepo
from datetime import datetime

router = Router()


async def send_subscriptions(message: Message, user_repo: UserRepo, sub_repo: SubscriptionRepo) -> None:
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    subs = await sub_repo.get_all(user.id) if user else []

    if not subs:
        await message.answer(
            "📭 <b>У вас нет подписок.</b>\n\n"
            "Оформите подписку через <b>🛒 Купить подписку</b>."
        )
        return

    now = datetime.utcnow()
    lines = ["🔑 <b>Ваши подписки:</b>\n"]

    for i, sub in enumerate(subs, start=1):
        is_active = sub.is_active and sub.expires_at > now
        status = "✅ Активна" if is_active else "❌ Истекла"
        lines.append(
            f"<b>#{i}</b> | Тариф: <code>{sub.tariff_id}</code>\n"
            f"   📅 С {sub.started_at.strftime('%d.%m.%Y')} по {sub.expires_at.strftime('%d.%m.%Y')}\n"
            f"   {status}"
        )

    await message.answer("\n\n".join(lines))