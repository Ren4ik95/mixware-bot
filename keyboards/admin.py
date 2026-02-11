from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.models import GateChannel, ModChannel
from typing import List


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎁 Выдать подписку", callback_data="admin_grant_sub"))
    builder.row(InlineKeyboardButton(text="📢 Gate-каналы (подписка)", callback_data="admin_gate_channels"))
    builder.row(InlineKeyboardButton(text="🎮 Мод-каналы (скачать мод)", callback_data="admin_mod_channels"))
    builder.row(InlineKeyboardButton(text="📨 Массовая рассылка", callback_data="admin_broadcast"))
    builder.row(InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close"))
    return builder.as_markup()


def gate_channels_keyboard(channels: List[GateChannel]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.row(InlineKeyboardButton(
            text=f"🗑 Удалить {ch.title}",
            callback_data=f"admin_del_gate:{ch.id}"
        ))
    builder.row(InlineKeyboardButton(text="➕ Добавить канал", callback_data="admin_add_gate"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back_to_panel"))
    return builder.as_markup()


def mod_channels_keyboard(channels: List[ModChannel]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        lock = "🔒" if ch.is_private else "🌐"
        builder.row(InlineKeyboardButton(
            text=f"🗑 Удалить {lock} {ch.title}",
            callback_data=f"admin_del_mod:{ch.id}"
        ))
    builder.row(InlineKeyboardButton(text="➕ Добавить мод-канал", callback_data="admin_add_mod"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back_to_panel"))
    return builder.as_markup()


def mod_channel_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌐 Публичный канал", callback_data="admin_mod_type:public"))
    builder.row(InlineKeyboardButton(text="🔒 Приватный канал", callback_data="admin_mod_type:private"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_mod_channels"))
    return builder.as_markup()


def grant_tariff_keyboard() -> InlineKeyboardMarkup:
    from core.config import TARIFFS
    builder = InlineKeyboardBuilder()
    for tariff in TARIFFS:
        builder.row(InlineKeyboardButton(
            text=f"📅 {tariff.label} — {tariff.price_usd}$",
            callback_data=f"admin_tariff:{tariff.id}"
        ))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back_to_panel"))
    return builder.as_markup()