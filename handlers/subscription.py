from aiogram import Router
from aiogram.types import CallbackQuery
from core.config import config
from db.engine import AsyncSessionFactory
from db.repository import GateChannelRepo
from utils.subscription import check_subscriptions_db
from keyboards.subscription import subscription_keyboard_db

router = Router()


@router.callback_query(lambda c: c.data == "check_subscription")
async def handle_check_subscription(callback: CallbackQuery) -> None:
    async with AsyncSessionFactory() as session:
        repo = GateChannelRepo(session)
        channels = await repo.get_all()

    not_subscribed = await check_subscriptions_db(
        bot=callback.bot,
        user_id=callback.from_user.id,
        channels=channels
    )

    if not_subscribed:
        await callback.answer("❌ Не все подписки выполнены", show_alert=True)
        await callback.message.edit_text(
            "❌ <b>Вы ещё не подписались на все каналы.</b>\n\nПодпишитесь и нажмите кнопку снова.",
            reply_markup=subscription_keyboard_db(not_subscribed)
        )
    else:
        await callback.answer("✅ Всё отлично!", show_alert=False)
        await callback.message.edit_text(
            "✅ <b>Подписки подтверждены!</b>\n\nНапишите /start для входа в бот."
        )