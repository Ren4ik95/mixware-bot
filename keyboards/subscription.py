from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.models import GateChannel
from typing import List


def subscription_keyboard_db(channels: List[GateChannel]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for channel in channels:
        builder.row(
            InlineKeyboardButton(
                text=f"📢 {channel.title}",
                url=f"https://t.me/{channel.username.lstrip('@')}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="✅ Проверить подписку",
            callback_data="check_subscription"
        )
    )

    return builder.as_markup()