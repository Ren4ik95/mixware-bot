from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.repository import UserRepo, PaymentRepo
from services.crypto_pay import crypto_pay

router = Router()

TOPUP_AMOUNTS = [1, 5, 10, 25, 50]


class TopupState(StatesGroup):
    waiting_payment = State()


def topup_keyboard() -> any:
    builder = InlineKeyboardBuilder()
    for amount in TOPUP_AMOUNTS:
        builder.row(InlineKeyboardButton(
            text=f"💵 {amount}$",
            callback_data=f"topup:{amount}"
        ))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="topup_back"))
    return builder.as_markup()


async def send_topup(message: Message) -> None:
    await message.answer(
        "🎰 <b>Пополнение баланса</b>\n\n"
        "Выберите сумму пополнения:",
        reply_markup=topup_keyboard()
    )


@router.callback_query(lambda c: c.data and c.data.startswith("topup:"))
async def handle_topup_amount(
    callback: CallbackQuery,
    state: FSMContext,
    user_repo: UserRepo,
    pay_repo: PaymentRepo,
) -> None:
    amount = float(callback.data.split(":")[1])
    user = await user_repo.get_or_create(
        callback.from_user.id,
        callback.from_user.full_name,
        callback.from_user.username,
    )

    try:
        invoice = await crypto_pay.create_invoice(
            amount=amount,
            description=f"Пополнение баланса | UID {callback.from_user.id}",
            payload=f"topup:{user.id}:{amount}",
        )
    except Exception:
        await callback.answer("Ошибка создания платежа. Попробуйте позже.", show_alert=True)
        return

    invoice_id = str(invoice["invoice_id"])
    pay_url = invoice["pay_url"]

    await pay_repo.create(
        user_id=user.id,
        invoice_id=invoice_id,
        tariff_id="topup",
        amount=amount,
    )

    await state.set_state(TopupState.waiting_payment)
    await state.update_data(invoice_id=invoice_id, amount=amount)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Оплатить через CryptoBot", url=pay_url))
    builder.row(InlineKeyboardButton(text="✅ Проверить оплату", callback_data="topup_check"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="topup_back"))

    await callback.answer()
    await callback.message.edit_text(
        f"💳 <b>Пополнение баланса</b>\n\n"
        f"💵 Сумма: <b>{amount}$</b>\n\n"
        f"Нажмите кнопку ниже для перехода к оплате.\n"
        f"После оплаты нажмите <b>✅ Проверить оплату</b>.",
        reply_markup=builder.as_markup()
    )


@router.callback_query(lambda c: c.data == "topup_check")
async def handle_topup_check(
    callback: CallbackQuery,
    state: FSMContext,
    user_repo: UserRepo,
    pay_repo: PaymentRepo,
) -> None:
    data = await state.get_data()
    invoice_id = data.get("invoice_id")
    amount = data.get("amount")

    if not invoice_id:
        await callback.answer("Платёж не найден. Начните заново.", show_alert=True)
        return

    invoices = await crypto_pay.get_invoice([invoice_id])

    if not invoices or invoices[0].get("status") != "paid":
        await callback.answer("❌ Оплата ещё не поступила.", show_alert=True)
        return

    payment = await pay_repo.get_by_invoice(invoice_id)
    if payment and payment.is_paid:
        await callback.answer("ℹ️ Баланс уже пополнен.", show_alert=True)
        return

    # Начисляем баланс (конвертируем $ в рубли — курс можно настроить)
    usd_to_rub = 90
    rub_amount = float(amount) * usd_to_rub

    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    user.balance += rub_amount
    await pay_repo.mark_paid(invoice_id)

    from db.engine import AsyncSessionFactory
    async with AsyncSessionFactory() as session:
        from sqlalchemy import update
        from db.models import User
        await session.execute(
            update(User)
            .where(User.telegram_id == callback.from_user.id)
            .values(balance=user.balance)
        )
        await session.commit()

    await state.clear()
    await callback.answer("✅ Баланс пополнен!", show_alert=True)
    await callback.message.edit_text(
        f"✅ <b>Баланс успешно пополнен!</b>\n\n"
        f"💵 Оплачено: <b>{amount}$</b>\n"
        f"💰 Начислено: <b>{rub_amount:.0f}₽</b>\n\n"
        f"Используйте /start для возврата в меню."
    )


@router.callback_query(lambda c: c.data == "topup_back")
async def handle_topup_back(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "🎰 <b>Пополнение баланса</b>\n\nВыберите сумму пополнения:",
        reply_markup=topup_keyboard()
    )