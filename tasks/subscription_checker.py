import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from db.engine import AsyncSessionFactory
from db.models import User, Subscription
from services.channel import kick_user_from_channel, is_user_in_channel
from sqlalchemy import select


async def notify_expiring_soon(bot: Bot) -> None:
    """Уведомляет пользователей за 24 часа до истечения подписки."""
    async with AsyncSessionFactory() as session:
        now = datetime.utcnow()
        soon = now + timedelta(hours=24)

        result = await session.execute(
            select(Subscription, User)
            .join(User, User.id == Subscription.user_id)
            .where(
                Subscription.is_active == True,
                Subscription.expires_at > now,
                Subscription.expires_at <= soon,
            )
        )
        rows = result.all()

    for sub, user in rows:
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    f"⚠️ <b>Внимание!</b>\n\n"
                    f"Ваша подписка истекает <b>{sub.expires_at.strftime('%d.%m.%Y в %H:%M')}</b>.\n\n"
                    f"Продлите подписку через <b>🛒 Купить подписку</b> чтобы не потерять доступ."
                )
            )
        except Exception as e:
            logging.warning(f"Не удалось уведомить {user.telegram_id}: {e}")


async def kick_expired_users(bot: Bot) -> None:
    """Кикает пользователей с истёкшей подпиской из приватных мод-каналов."""
    async with AsyncSessionFactory() as session:
        now = datetime.utcnow()

        result = await session.execute(
            select(Subscription, User)
            .join(User, User.id == Subscription.user_id)
            .where(
                Subscription.is_active == True,
                Subscription.expires_at <= now,
            )
        )
        rows = result.all()

        # Получаем приватные мод-каналы
        from db.repository import ModChannelRepo
        mod_repo = ModChannelRepo(session)
        private_channels = await mod_repo.get_private_channels()

        for sub, user in rows:
            sub.is_active = False

            if not private_channels:
                continue

            for ch in private_channels:
                if not ch.channel_id:
                    continue

                in_channel = await is_user_in_channel(bot, user.telegram_id, ch.channel_id)

                if in_channel:
                    kicked = await kick_user_from_channel(bot, user.telegram_id, ch.channel_id)

                    if kicked:
                        try:
                            await bot.send_message(
                                chat_id=user.telegram_id,
                                text=(
                                    "🔒 <b>Подписка истекла</b>\n\n"
                                    f"Ваш доступ к каналу <b>{ch.title}</b> закрыт.\n\n"
                                    "Чтобы восстановить доступ — оформите новую подписку "
                                    "через <b>🛒 Купить подписку</b>."
                                )
                            )
                        except Exception as e:
                            logging.warning(f"Не удалось уведомить {user.telegram_id}: {e}")

        await session.commit()

    logging.info(f"Проверка подписок завершена. Обработано: {len(rows)}")


async def run_subscription_checker(bot: Bot) -> None:
    """Фоновая задача — запускается раз в день."""
    logging.info("Запущена фоновая проверка подписок")
    while True:
        try:
            await notify_expiring_soon(bot)
            await kick_expired_users(bot)
        except Exception as e:
            logging.error(f"Ошибка в subscription_checker: {e}")
        await asyncio.sleep(60 * 60 * 24)