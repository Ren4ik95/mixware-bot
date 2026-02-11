from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from db.repository import UserRepo, SubscriptionRepo, ModChannelRepo
from keyboards.menu import main_menu_keyboard
from core.config import config

router = Router()


async def show_main_menu(message: Message, user_repo: UserRepo, sub_repo: SubscriptionRepo) -> None:
    tg_user = message.from_user
    user = await user_repo.get_or_create(tg_user.id, tg_user.full_name, tg_user.username)
    active_sub = await sub_repo.get_active(user.id)
    sub_count = len(await sub_repo.get_all(user.id))
    is_admin = tg_user.id in config.admin_ids

    text = (
        f"🖥 <b>Личный Кабинет</b>\n\n"
        f"🆔 UID: <code>{tg_user.id}</code>\n"
        f"💰 Баланс: <b>{user.balance:.0f}₽</b>\n"
        f"🔑 Подписок: <b>{sub_count}</b>\n"
        f"📅 Активна до: <b>{'нет' if not active_sub else ('Навсегда' if active_sub.expires_at.year == 9999 else active_sub.expires_at.strftime('%d.%m.%Y'))}</b>"
    )

    await message.answer(text, reply_markup=main_menu_keyboard(is_admin=is_admin))


@router.message(CommandStart())
async def handle_start(message: Message, user_repo: UserRepo, sub_repo: SubscriptionRepo) -> None:
    await show_main_menu(message, user_repo, sub_repo)


@router.message(F.text == "📥 Скачать мод")
async def handle_mod(message: Message, user_repo: UserRepo, sub_repo: SubscriptionRepo, mod_repo: ModChannelRepo) -> None:
    from handlers.mod import send_mod
    await send_mod(message, user_repo, sub_repo, mod_repo)


@router.message(F.text == "🔧 Мои подписки")
async def handle_subs(message: Message, user_repo: UserRepo, sub_repo: SubscriptionRepo) -> None:
    from handlers.my_subscriptions import send_subscriptions
    await send_subscriptions(message, user_repo, sub_repo)


@router.message(F.text == "🛒 Купить подписку")
async def handle_buy(message: Message) -> None:
    from handlers.payment import send_tariffs
    await send_tariffs(message)


@router.message(F.text == "🎰 Пополнить баланс")
async def handle_topup(message: Message) -> None:
    from handlers.topup import send_topup
    await send_topup(message)


@router.message(F.text == "🌐 Купить ВПН")
async def handle_vpn(message: Message) -> None:
    from handlers.vpn import send_vpn_menu
    await send_vpn_menu(message)