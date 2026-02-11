from aiogram import Router
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.repository import UserRepo, SubscriptionRepo, ModChannelRepo
from services.channel import create_invite_link
import logging

router = Router()

NO_SUB_TEXT = (
    "🔒 <b>Доступ ограничен</b>\n\n"
    "Для скачивания мода необходима активная подписка.\n"
    "Нажмите <b>🛒 Купить подписку</b> для оформления."
)

SUB_EXPIRED_TEXT = (
    "❌ <b>Подписка истекла</b>\n\n"
    "Ваша подписка закончилась. Доступ к моду закрыт.\n\n"
    "Оформите новую подписку через <b>🛒 Купить подписку</b>."
)

NO_MOD_TEXT = (
    "🔧 <b>Мод временно недоступен</b>\n\n"
    "Файл мода ещё не добавлен. Следите за обновлениями!"
)


async def send_mod(
    message: Message,
    user_repo: UserRepo,
    sub_repo: SubscriptionRepo,
    mod_repo: ModChannelRepo
) -> None:
    from core.config import config
    from core.bot import bot

    is_admin = message.from_user.id in config.admin_ids
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    active_sub = await sub_repo.get_active(user.id) if user else None

    if not active_sub and not is_admin:
        all_subs = await sub_repo.get_all(user.id) if user else []
        await message.answer(SUB_EXPIRED_TEXT if all_subs else NO_SUB_TEXT)
        return

    mod_channels = await mod_repo.get_all()

    if not mod_channels:
        await message.answer(NO_MOD_TEXT)
        return

    builder = InlineKeyboardBuilder()

    for ch in mod_channels:
        if ch.is_private and ch.channel_id:
            try:
                invite_link = await create_invite_link(bot, ch.channel_id)
                url = invite_link
            except Exception as e:
                logging.error(f"Ошибка генерации инвайта для {ch.channel_id}: {e}")
                url = ch.url
        else:
            url = ch.url

        builder.row(InlineKeyboardButton(text=f"📥 {ch.title}", url=url))

    expires_text = ""
    if active_sub:
        expires_text = (
            "\n📅 Подписка: <b>Навсегда</b>"
            if active_sub.expires_at.year == 9999
            else f"\n📅 Подписка до: <b>{active_sub.expires_at.strftime('%d.%m.%Y %H:%M')}</b>"
        )

    await message.answer(
        f"✅ <b>Доступ открыт!</b>\n\n"
        f"Нажмите кнопку для скачивания мода.\n"
        f"⚠️ Ссылка одноразовая — не передавайте её другим.{expires_text}",
        reply_markup=builder.as_markup()
    )