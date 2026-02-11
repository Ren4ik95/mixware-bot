import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError


async def create_invite_link(bot: Bot, channel_id: int) -> str:
    """Создаёт одноразовую ссылку-приглашение в приватный канал."""
    try:
        link = await bot.create_chat_invite_link(
            chat_id=channel_id,
            member_limit=1,
            creates_join_request=False
        )
        return link.invite_link
    except Exception as e:
        logging.error(f"Ошибка создания инвайт-ссылки для {channel_id}: {e}")
        raise


async def kick_user_from_channel(bot: Bot, telegram_id: int, channel_id: int) -> bool:
    """Кикает пользователя из канала."""
    try:
        await bot.ban_chat_member(chat_id=channel_id, user_id=telegram_id)
        await bot.unban_chat_member(chat_id=channel_id, user_id=telegram_id, only_if_banned=True)
        return True
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        logging.warning(f"Не удалось кикнуть {telegram_id} из {channel_id}: {e}")
        return False


async def is_user_in_channel(bot: Bot, telegram_id: int, channel_id: int) -> bool:
    """Проверяет состоит ли пользователь в канале."""
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=telegram_id)
        return member.status not in ("left", "kicked", "banned")
    except Exception:
        return False