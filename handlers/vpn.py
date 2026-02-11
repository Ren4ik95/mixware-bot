from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.vpn import vpn_countries_keyboard, vpn_pay_keyboard, VPN_SERVERS, RUB_TO_USD, get_server
from db.repository import UserRepo, PaymentRepo
from services.crypto_pay import crypto_pay

router = Router()


VPN_CONFIGS = {
    "fi": (
        "🇫🇮 <b>Finland VPN — конфиг готов!</b>\n\n"
        "📋 Скопируй код ниже и вставь в своё VPN-приложение "
        "(например <b>V2RayTun</b>, <b>Nekobox</b>, <b>Hiddify</b>):\n\n"
        "<code>vless://a7a9f670-44c0-45a9-8047-69db0203c142@45.144.53.68:443/?type=tcp&encryption=none&flow=&security=tls&sni=ficdn13.suio.me&allowInsecure=1#🇫🇮Finland%209290%20vless%20@Extra_Mods</code>"
    ),
    "de": (
        "🇩🇪 <b>Germany VPN — конфиг готов!</b>\n\n"
        "📋 Скопируй код ниже и вставь в своё VPN-приложение "
        "(например <b>V2RayTun</b>, <b>Nekobox</b>, <b>Hiddify</b>):\n\n"
        "<code>ss://a7a9f670-44c0-45a9-8047-69db0203c142@decdn13.suio.me:443/?type=tcp&encryption=none&flow=&security=tls&sni=decdn13.suio.me&allowInsecure=1#🇩🇪Germany%204917%20outline%20@Extra_Mods</code>"
    ),
    "it": (
        "🇮🇹 <b>Italy VPN — конфиг готов!</b>\n\n"
        "📋 Скопируй код ниже и вставь в своё VPN-приложение "
        "(например <b>V2RayTun</b>, <b>Nekobox</b>, <b>Hiddify</b>):\n\n"
        "<code>vless://c38e6142-9223-47ef-84ce-2a84a308cafb@217.12.219.51:443/?type=tcp&encryption=none&flow=xtls-rprx-vision&sni=ozon.ru&fp=chrome&security=reality&pbk=FkmYFobwxLMLEktYXywmjthuEYCZggITsxwPNasTKUg&sid=65ce6cee3941af69#🇮🇹Italy%209015%20vless%20@Extra_Mods</code>"
    ),
    "md": (
        "🇲🇩 <b>Moldova VPN — конфиг готов!</b>\n\n"
        "📋 Скопируй код ниже и вставь в своё VPN-приложение "
        "(например <b>V2RayTun</b>, <b>Nekobox</b>, <b>Hiddify</b>):\n\n"
        "<code>vless://a619d576-1380-4aac-8732-99e8dfe8df0f@mlb.tunnelguard.ru:443/?type=tcp&encryption=none&flow=xtls-rprx-vision&security=tls&sni=mlb.tunnelguard.ru&alpn=h2%2Chttp%2F1.1&allowInsecure=1&fp=random#🇲🇩Moldova%207513%20vless%20@Extra_Mods</code>"
    ),
    "nl": (
        "🇳🇱 <b>Netherlands VPN — конфиг готов!</b>\n\n"
        "📋 Скопируй код ниже и вставь в своё VPN-приложение "
        "(например <b>V2RayTun</b>, <b>Nekobox</b>, <b>Hiddify</b>):\n\n"
        "<code>vless://a44e0875-210f-4941-9062-89b6361a14c6@91.84.102.165:443/?type=tcp&encryption=none&flow=xtls-rprx-vision&sni=apple.com&security=reality&pbk=i5a8i2AWUSMZ-rYA6hGBRCBBoe7W5ah33SCdF5JkMk4&sid=8bcfe256cf216fd8#🇳🇱Netherlands%201212%20vless%20@Extra_Mods</code>"
    ),
    "ru": (
        "🇷🇺 <b>Russia VPN — конфиг готов!</b>\n\n"
        "📋 Скопируй код ниже и вставь в своё VPN-приложение "
        "(например <b>V2RayTun</b>, <b>Nekobox</b>, <b>Hiddify</b>):\n\n"
        "<code>vless://57df620f-96b1-4f2b-a6ff-043ce11b6995@moscow.pryanik.net.ru:4443/?type=tcp&encryption=none&flow=xtls-rprx-vision&sni=ozon.ru&fp=chrome&security=reality&pbk=DLqBw8458S7vERpm_w4NMGz1kNp7b7uIjwCgStZERyo&sid=#🇷🇺Russia%207272%20vless%20@Extra_Mods</code>"
    ),
    "jp": (
        "🇯🇵 <b>Japan VPN — конфиг готов!</b>\n\n"
        "📋 Скопируй код ниже и вставь в своё VPN-приложение "
        "(например <b>V2RayTun</b>, <b>Nekobox</b>, <b>Hiddify</b>).\n\n"
        "⚠️ Сервер будет добавлен в ближайшее время."
    ),
}


class VpnState(StatesGroup):
    waiting_payment = State()


async def send_vpn_menu(message: Message) -> None:
    from core.config import config

    if message.from_user.id in config.admin_ids:
        await message.answer(
            "🌐 <b>ВПН — режим админа</b>\n\n"
            "Выберите страну чтобы получить конфиг:",
            reply_markup=vpn_countries_keyboard()
        )
        return

    await message.answer(
        "🌐 <b>Купить ВПН</b>\n\n"
        "Выберите страну сервера:\n\n"
        "💡 После оплаты вы получите конфиг для подключения.",
        reply_markup=vpn_countries_keyboard()
    )


@router.callback_query(lambda c: c.data and c.data.startswith("vpn_buy:"))
async def handle_vpn_buy(
    callback: CallbackQuery,
    state: FSMContext,
    user_repo: UserRepo,
    pay_repo: PaymentRepo,
) -> None:
    from core.config import config

    server_id = callback.data.split(":")[1]
    server = get_server(server_id)

    if not server:
        await callback.answer("Сервер не найден.", show_alert=True)
        return

    # Админу сразу выдаём конфиг без оплаты
    if callback.from_user.id in config.admin_ids:
        await callback.answer()
        config_text = VPN_CONFIGS.get(server_id, "⚠️ Конфиг не найден.")
        await callback.message.answer(config_text)
        return

    user = await user_repo.get_or_create(
        callback.from_user.id,
        callback.from_user.full_name,
        callback.from_user.username,
    )

    price_usd = round(server["price_rub"] * RUB_TO_USD, 2)

    try:
        invoice = await crypto_pay.create_invoice(
            amount=price_usd,
            description=f"VPN {server['flag']} {server['country']} | UID {callback.from_user.id}",
            payload=f"vpn:{user.id}:{server_id}",
        )
    except Exception as e:
        await callback.answer("Ошибка создания платежа. Попробуйте позже.", show_alert=True)
        import logging
        logging.error(f"VPN CryptoPay error: {e}")
        return

    invoice_id = str(invoice["invoice_id"])
    pay_url = invoice["pay_url"]

    await pay_repo.create(
        user_id=user.id,
        invoice_id=invoice_id,
        tariff_id=f"vpn_{server_id}",
        amount=price_usd,
    )

    await state.set_state(VpnState.waiting_payment)
    await state.update_data(invoice_id=invoice_id, server_id=server_id)

    await callback.answer()
    await callback.message.edit_text(
        f"💳 <b>Оформление ВПН</b>\n\n"
        f"{server['flag']} Страна: <b>{server['country']}</b>\n"
        f"💰 Сумма: <b>{server['price_rub']}₽</b> (~{price_usd}$)\n\n"
        f"Нажмите кнопку ниже для оплаты через CryptoBot.\n"
        f"После оплаты нажмите <b>✅ Проверить оплату</b>.",
        reply_markup=vpn_pay_keyboard(pay_url)
    )


@router.callback_query(lambda c: c.data == "vpn_check_payment")
async def handle_vpn_check_payment(
    callback: CallbackQuery,
    state: FSMContext,
    pay_repo: PaymentRepo,
) -> None:
    data = await state.get_data()
    invoice_id = data.get("invoice_id")
    server_id = data.get("server_id")

    if not invoice_id:
        await callback.answer("Платёж не найден. Начните заново.", show_alert=True)
        return

    invoices = await crypto_pay.get_invoice([invoice_id])

    if not invoices:
        await callback.answer("Информация о платеже не найдена.", show_alert=True)
        return

    if invoices[0].get("status") != "paid":
        await callback.answer("❌ Оплата ещё не поступила. Повторите попытку.", show_alert=True)
        return

    payment = await pay_repo.get_by_invoice(invoice_id)
    if payment and payment.is_paid:
        await callback.answer("ℹ️ Конфиг уже был выдан.", show_alert=True)
        config_text = VPN_CONFIGS.get(server_id, "⚠️ Конфиг не найден.")
        await callback.message.answer(config_text)
        return

    await pay_repo.mark_paid(invoice_id)
    await state.clear()

    config_text = VPN_CONFIGS.get(server_id, "⚠️ Конфиг не найден. Обратитесь к администратору.")

    await callback.answer("✅ Оплата получена!", show_alert=True)
    await callback.message.edit_text("✅ <b>Оплата прошла успешно!</b>\n\nВаш VPN конфиг готов 👇")
    await callback.message.answer(config_text)


@router.callback_query(lambda c: c.data == "vpn_back")
async def handle_vpn_back(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        "🌐 <b>Купить ВПН</b>\n\n"
        "Выберите страну сервера:\n\n"
        "💡 После оплаты вы получите конфиг для подключения.",
        reply_markup=vpn_countries_keyboard()
    )