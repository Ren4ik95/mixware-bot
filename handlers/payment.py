from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.repository import UserRepo, SubscriptionRepo, PaymentRepo
from services.crypto_pay import crypto_pay
from keyboards.payment import tariffs_keyboard, pay_keyboard
from core.config import TARIFFS

router = Router()


class PaymentState(StatesGroup):
    waiting_payment = State()


def get_tariff(tariff_id: str):
    return next((t for t in TARIFFS if t.id == tariff_id), None)


async def send_tariffs(message: Message) -> None:
    await message.answer(
        "🛒 <b>Выберите тариф подписки:</b>\n\n"
        "После выбора вы будете перенаправлены для оплаты через CryptoBot.",
        reply_markup=tariffs_keyboard()
    )


@router.callback_query(lambda c: c.data and c.data.startswith("tariff:"))
async def handle_tariff_select(
    callback: CallbackQuery,
    state: FSMContext,
    user_repo: UserRepo,
    pay_repo: PaymentRepo,
) -> None:
    tariff_id = callback.data.split(":")[1]
    tariff = get_tariff(tariff_id)

    if not tariff:
        await callback.answer("Тариф не найден", show_alert=True)
        return

    user = await user_repo.get_or_create(
        callback.from_user.id,
        callback.from_user.full_name,
        callback.from_user.username,
    )

    try:
        invoice = await crypto_pay.create_invoice(
            amount=tariff.price_usd,
            description=f"Подписка {tariff.label} | UID {callback.from_user.id}",
            payload=f"{user.id}:{tariff.id}",
        )
    except Exception as e:
        await callback.answer("Ошибка создания платежа. Попробуйте позже.", show_alert=True)
        import logging
        logging.error(f"CryptoPay error: {e}")
        return

    invoice_id = str(invoice["invoice_id"])
    pay_url = invoice["pay_url"]

    await pay_repo.create(
        user_id=user.id,
        invoice_id=invoice_id,
        tariff_id=tariff.id,
        amount=tariff.price_usd,
    )

    await state.set_state(PaymentState.waiting_payment)
    await state.update_data(invoice_id=invoice_id, tariff_id=tariff.id)

    await callback.answer()
    await callback.message.edit_text(
        f"💳 <b>Оформление подписки</b>\n\n"
        f"📅 Тариф: <b>{tariff.label}</b>\n"
        f"💵 Сумма: <b>{tariff.price_usd}$</b>\n\n"
        f"Нажмите кнопку ниже для перехода к оплате через CryptoBot.\n"
        f"После оплаты нажмите <b>✅ Проверить оплату</b>.",
        reply_markup=pay_keyboard(pay_url)
    )


@router.callback_query(lambda c: c.data == "check_payment")
async def handle_check_payment(
    callback: CallbackQuery,
    state: FSMContext,
    user_repo: UserRepo,
    sub_repo: SubscriptionRepo,
    pay_repo: PaymentRepo,
) -> None:
    data = await state.get_data()
    invoice_id = data.get("invoice_id")
    tariff_id = data.get("tariff_id")

    if not invoice_id:
        await callback.answer("Платёж не найден. Начните заново.", show_alert=True)
        return

    invoices = await crypto_pay.get_invoice([invoice_id])

    if not invoices:
        await callback.answer("Информация о платеже не найдена.", show_alert=True)
        return

    invoice = invoices[0]

    if invoice.get("status") != "paid":
        await callback.answer("❌ Оплата ещё не поступила. Повторите попытку.", show_alert=True)
        return

    payment = await pay_repo.get_by_invoice(invoice_id)
    if payment and payment.is_paid:
        await callback.answer("ℹ️ Подписка уже активирована.", show_alert=True)
        return

    tariff = get_tariff(tariff_id)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)

    await sub_repo.create(
        user_id=user.id,
        tariff_id=tariff.id,
        months=tariff.months,
        days=tariff.days,
        hours=tariff.hours,
        is_infinite=tariff.is_infinite
    )
    await pay_repo.mark_paid(invoice_id)
    await state.clear()

    expires_text = "Навсегда" if tariff.is_infinite else f"до {(await sub_repo.get_active(user.id)).expires_at.strftime('%d.%m.%Y %H:%M')}"

    await callback.answer("✅ Подписка активирована!", show_alert=True)
    await callback.message.edit_text(
        f"🎉 <b>Подписка успешно оформлена!</b>\n\n"
        f"📅 Тариф: <b>{tariff.label}</b>\n"
        f"💵 Оплачено: <b>{tariff.price_usd}$</b>\n"
        f"📆 Действует: <b>{expires_text}</b>\n\n"
        f"Используйте /start для возврата в меню."
    )