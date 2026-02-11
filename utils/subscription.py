from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from db.models import GateChannel
from typing import List
import logging


async def check_subscriptions_db(bot: Bot, user_id: int, channels: List[GateChannel]) -> List[GateChannel]:
    """Возвращает каналы на которые пользователь НЕ подписан."""
    not_subscribed = []

    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel.username, user_id=user_id)
            logging.info(f"Канал {channel.username} | Статус: {member.status}")
            if member.status in ("left", "kicked", "banned"):
                not_subscribed.append(channel)
        except (TelegramForbiddenError, TelegramBadRequest) as e:
            logging.warning(f"Ошибка проверки канала {channel.username}: {e}")
            not_subscribed.append(channel)

    return not_subscribed