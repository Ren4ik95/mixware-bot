from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.config import TARIFFS


def tariffs_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tariff in TARIFFS:
        builder.row(
            InlineKeyboardButton(
                text=f"📅 {tariff.label} — {tariff.price_usd}$",
                callback_data=f"tariff:{tariff.id}"
            )
        )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu"))
    return builder.as_markup()


def pay_keyboard(pay_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Оплатить через CryptoBot", url=pay_url))
    builder.row(InlineKeyboardButton(text="✅ Проверить оплату", callback_data="check_payment"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_subscription"))
    return builder.as_markup()