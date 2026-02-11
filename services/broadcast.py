import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest


async def broadcast(bot: Bot, user_ids: list[int], text: str) -> tuple[int, int]:
    """
    Рассылает сообщение всем пользователям.
    Возвращает (успешно, ошибок).
    """
    success = 0
    failed = 0

    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=text)
            success += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        except Exception as e:
            logging.warning(f"Broadcast error for {user_id}: {e}")
            failed += 1

        # Небольшая задержка чтобы не получить флуд-бан
        await asyncio.sleep(0.05)

    return success, failed