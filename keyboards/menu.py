from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="📥 Скачать мод")],
        [KeyboardButton(text="🔧 Мои подписки")],
        [KeyboardButton(text="🎰 Пополнить баланс")],
        [KeyboardButton(text="🛒 Купить подписку")],
        [KeyboardButton(text="🌐 Купить ВПН")],
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text="👮 Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)