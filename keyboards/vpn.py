from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


VPN_SERVERS = [
    {"id": "nl", "flag": "🇳🇱", "country": "Netherlands", "price_rub": 15},
    {"id": "de", "flag": "🇩🇪", "country": "Germany",     "price_rub": 20},
    {"id": "ru", "flag": "🇷🇺", "country": "Russia",      "price_rub": 20},
    {"id": "md", "flag": "🇲🇩", "country": "Moldova",     "price_rub": 10},
    {"id": "fi", "flag": "🇫🇮", "country": "Finland",     "price_rub": 15},
    {"id": "jp", "flag": "🇯🇵", "country": "Japan",       "price_rub": 15},
    {"id": "it", "flag": "🇮🇹", "country": "Italy",       "price_rub": 15},
]

# Курс рубля к доллару (можно вынести в .env)
RUB_TO_USD = 0.011


def get_server(server_id: str) -> dict | None:
    return next((s for s in VPN_SERVERS if s["id"] == server_id), None)


def vpn_countries_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for server in VPN_SERVERS:
        price_usd = round(server["price_rub"] * RUB_TO_USD, 2)
        builder.row(InlineKeyboardButton(
            text=f"{server['flag']} {server['country']} — {server['price_rub']}₽ / 1 Server",
            callback_data=f"vpn_buy:{server['id']}"
        ))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="vpn_back"))
    return builder.as_markup()


def vpn_pay_keyboard(pay_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Оплатить через CryptoBot", url=pay_url))
    builder.row(InlineKeyboardButton(text="✅ Проверить оплату", callback_data="vpn_check_payment"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="vpn_back"))
    return builder.as_markup()