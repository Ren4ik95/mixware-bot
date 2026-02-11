import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.config import config, TARIFFS
from db.repository import UserRepo, SubscriptionRepo, GateChannelRepo, ModChannelRepo
from keyboards.admin import (
    admin_menu_keyboard,
    gate_channels_keyboard,
    mod_channels_keyboard,
    mod_channel_type_keyboard,
    grant_tariff_keyboard,
)
from services.broadcast import broadcast

router = Router()

MIN_GATE_CHANNELS = 1


def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids


def get_tariff(tariff_id: str):
    return next((t for t in TARIFFS if t.id == tariff_id), None)


class AdminState(StatesGroup):
    grant_waiting_user_id = State()

    add_gate_username = State()
    add_gate_title = State()

    add_mod_title = State()
    add_mod_username = State()
    add_mod_url = State()
    add_mod_channel_id = State()

    broadcast_text = State()


# ─── Открыть панель ───────────────────────────────────────────────────────────

@router.message(F.text == "👮 Админ-панель")
async def handle_admin_panel(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Нет доступа.")
        return
    await message.answer(
        "👮 <b>Админ-панель</b>\n\nВыберите действие:",
        reply_markup=admin_menu_keyboard()
    )


@router.callback_query(lambda c: c.data == "admin_back_to_panel")
async def back_to_panel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        "👮 <b>Админ-панель</b>\n\nВыберите действие:",
        reply_markup=admin_menu_keyboard()
    )


@router.callback_query(lambda c: c.data == "admin_close")
async def admin_close(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.delete()


# ─── Выдача подписки ──────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "admin_grant_sub")
async def handle_grant_sub(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа.", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(
        "🎁 <b>Выдача подписки</b>\n\nВыберите тариф:",
        reply_markup=grant_tariff_keyboard()
    )


@router.callback_query(lambda c: c.data and c.data.startswith("admin_tariff:"))
async def handle_grant_tariff(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    tariff_id = callback.data.split(":")[1]
    tariff = get_tariff(tariff_id)
    if not tariff:
        await callback.answer("Тариф не найден.", show_alert=True)
        return
    await state.set_state(AdminState.grant_waiting_user_id)
    await state.update_data(tariff_id=tariff_id)
    await callback.answer()
    await callback.message.edit_text(
        f"🎁 Тариф: <b>{tariff.label}</b>\n\n"
        f"Введите <b>Telegram ID</b> пользователя:\n"
        f"<i>Узнать ID можно у @userinfobot</i>"
    )


@router.message(AdminState.grant_waiting_user_id)
async def handle_grant_user_id(
    message: Message,
    state: FSMContext,
    user_repo: UserRepo,
    sub_repo: SubscriptionRepo
) -> None:
    if not is_admin(message.from_user.id):
        return
    if not message.text or not message.text.strip().isdigit():
        await message.answer("⚠️ Введите корректный Telegram ID (только цифры).")
        return
    target_id = int(message.text.strip())
    data = await state.get_data()
    tariff = get_tariff(data["tariff_id"])
    target_user = await user_repo.get_by_telegram_id(target_id)
    if not target_user:
        await message.answer(
            f"❌ Пользователь <code>{target_id}</code> не найден.\n"
            f"Он должен хотя бы раз написать боту."
        )
        await state.clear()
        return
    sub = await sub_repo.create(
        user_id=target_user.id,
        tariff_id=tariff.id,
        months=tariff.months,
        days=tariff.days,
        hours=tariff.hours,
        is_infinite=tariff.is_infinite
    )
    await state.clear()
    expires_text = "Навсегда" if tariff.is_infinite else sub.expires_at.strftime('%d.%m.%Y %H:%M')
    await message.answer(
        f"✅ <b>Подписка выдана!</b>\n\n"
        f"👤 Пользователь: <code>{target_id}</code>\n"
        f"📅 Тариф: <b>{tariff.label}</b>\n"
        f"📆 До: <b>{expires_text}</b>",
        reply_markup=admin_menu_keyboard()
    )
    try:
        from core.bot import bot
        await bot.send_message(
            chat_id=target_id,
            text=(
                f"🎁 <b>Вам выдана подписка!</b>\n\n"
                f"📅 Тариф: <b>{tariff.label}</b>\n"
                f"📆 До: <b>{expires_text}</b>"
            )
        )
    except Exception:
        pass


# ─── Gate-каналы ──────────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "admin_gate_channels")
async def handle_gate_channels(callback: CallbackQuery, gate_repo: GateChannelRepo) -> None:
    if not is_admin(callback.from_user.id):
        return
    channels = await gate_repo.get_all()
    text = (
        f"📢 <b>Gate-каналы</b> (подписка при входе)\n\n"
        f"Текущих каналов: <b>{len(channels)}</b>\n"
        f"⚠️ Минимум: <b>{MIN_GATE_CHANNELS}</b>\n\n"
    )
    text += "\n".join(f"• {ch.title} ({ch.username})" for ch in channels) if channels else "Каналов нет."
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=gate_channels_keyboard(channels))


@router.callback_query(lambda c: c.data == "admin_add_gate")
async def handle_add_gate_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminState.add_gate_username)
    await callback.answer()
    await callback.message.edit_text(
        "📢 <b>Добавление gate-канала</b>\n\n"
        "⚠️ <b>Важно:</b> перед добавлением убедитесь что бот уже добавлен "
        "в канал как <b>администратор</b> с правом просмотра участников.\n\n"
        "Введите username канала:\n<code>@username</code>"
    )


@router.message(AdminState.add_gate_username)
async def handle_add_gate_username(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    username = message.text.strip()
    if not username.startswith("@"):
        await message.answer("⚠️ Username должен начинаться с @\nПример: <code>@mychannel</code>")
        return
    await state.update_data(gate_username=username)
    await state.set_state(AdminState.add_gate_title)
    await message.answer(f"✅ Username: <b>{username}</b>\n\nВведите <b>название кнопки</b>:")


@router.message(AdminState.add_gate_title)
async def handle_add_gate_title(message: Message, state: FSMContext, gate_repo: GateChannelRepo) -> None:
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    title = message.text.strip()
    await gate_repo.add(username=data["gate_username"], title=title)
    await state.clear()
    channels = await gate_repo.get_all()
    await message.answer(
        f"✅ <b>Канал добавлен!</b>\n\n"
        f"📢 {title} ({data['gate_username']})\n"
        f"Всего каналов: <b>{len(channels)}</b>",
        reply_markup=admin_menu_keyboard()
    )


@router.callback_query(lambda c: c.data and c.data.startswith("admin_del_gate:"))
async def handle_del_gate(callback: CallbackQuery, gate_repo: GateChannelRepo) -> None:
    if not is_admin(callback.from_user.id):
        return
    count = await gate_repo.count()
    if count <= MIN_GATE_CHANNELS:
        await callback.answer(
            f"⛔️ Нельзя удалить! Минимум каналов: {MIN_GATE_CHANNELS}.\n"
            f"Сначала добавьте новый канал.",
            show_alert=True
        )
        return
    channel_id = int(callback.data.split(":")[1])
    await gate_repo.remove(channel_id)
    channels = await gate_repo.get_all()
    await callback.answer("✅ Канал удалён")
    text = f"📢 <b>Gate-каналы</b>\n\nТекущих каналов: <b>{len(channels)}</b>\n\n"
    text += "\n".join(f"• {ch.title} ({ch.username})" for ch in channels) if channels else "Каналов нет."
    await callback.message.edit_text(text, reply_markup=gate_channels_keyboard(channels))


# ─── Мод-каналы ───────────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "admin_mod_channels")
async def handle_mod_channels(callback: CallbackQuery, mod_repo: ModChannelRepo) -> None:
    if not is_admin(callback.from_user.id):
        return
    channels = await mod_repo.get_all()
    text = f"🎮 <b>Мод-каналы</b>\n\nТекущих каналов: <b>{len(channels)}</b>\n\n"
    if channels:
        for ch in channels:
            lock = "🔒 Приватный" if ch.is_private else "🌐 Публичный"
            text += f"• {ch.title} — {lock}\n"
    else:
        text += "⚠️ Каналов нет — юзеры увидят сообщение что мод недоступен."
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=mod_channels_keyboard(channels))


@router.callback_query(lambda c: c.data == "admin_add_mod")
async def handle_add_mod_type(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await callback.message.edit_text(
        "🎮 <b>Добавление мод-канала</b>\n\n"
        "⚠️ <b>Важно:</b> перед добавлением убедитесь что бот уже добавлен "
        "в канал как <b>администратор</b> с правами:\n"
        "• Добавление участников\n"
        "• Удаление участников\n\n"
        "Выберите тип канала:",
        reply_markup=mod_channel_type_keyboard()
    )


@router.callback_query(lambda c: c.data and c.data.startswith("admin_mod_type:"))
async def handle_mod_type_select(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    channel_type = callback.data.split(":")[1]
    is_private = channel_type == "private"
    await state.update_data(mod_is_private=is_private)
    await state.set_state(AdminState.add_mod_title)
    await callback.answer()

    if is_private:
        await callback.message.edit_text(
            "🔒 <b>Добавление приватного канала</b>\n\n"
            "Шаги:\n"
            "1️⃣ Название кнопки\n"
            "2️⃣ Числовой ID канала\n"
            "3️⃣ Инвайт-ссылка\n\n"
            "Введите <b>название кнопки</b>:\n"
            "<i>Например: Скачать мод v1.5</i>"
        )
    else:
        await callback.message.edit_text(
            "🌐 <b>Добавление публичного канала</b>\n\n"
            "Шаги:\n"
            "1️⃣ Название кнопки\n"
            "2️⃣ Username канала\n"
            "3️⃣ Ссылка\n\n"
            "Введите <b>название кнопки</b>:\n"
            "<i>Например: Скачать мод v1.5</i>"
        )


@router.message(AdminState.add_mod_title)
async def handle_add_mod_title(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.update_data(mod_title=message.text.strip())
    data = await state.get_data()

    if data.get("mod_is_private"):
        await state.set_state(AdminState.add_mod_channel_id)
        await message.answer(
            f"✅ Название: <b>{message.text.strip()}</b>\n\n"
            f"Введите числовой <b>ID канала</b>:\n"
            f"<i>Начинается с -100, например: -1001234567890\n"
            f"Узнать ID: перешли сообщение из канала боту @userinfobot</i>"
        )
    else:
        await state.set_state(AdminState.add_mod_username)
        await message.answer(
            f"✅ Название: <b>{message.text.strip()}</b>\n\n"
            f"Введите username канала:\n<code>@username</code>"
        )


@router.message(AdminState.add_mod_channel_id)
async def handle_add_mod_channel_id(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    raw = message.text.strip()
    if not raw.lstrip("-").isdigit():
        await message.answer(
            "⚠️ Введите корректный ID канала\n"
            "<i>Например: -1001234567890</i>"
        )
        return
    await state.update_data(mod_channel_id=int(raw), mod_username="private")
    await state.set_state(AdminState.add_mod_url)
    await message.answer(
        f"✅ ID канала: <code>{raw}</code>\n\n"
        f"Введите инвайт-ссылку канала:\n"
        f"<i>Настройки канала → Пригласительная ссылка\n"
        f"Выглядит как: https://t.me/+xxxxxxxxxx</i>"
    )


@router.message(AdminState.add_mod_username)
async def handle_add_mod_username(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    username = message.text.strip()
    if not username.startswith("@"):
        await message.answer("⚠️ Username должен начинаться с @")
        return
    await state.update_data(mod_username=username)
    await state.set_state(AdminState.add_mod_url)
    await message.answer(
        f"✅ Username: <b>{username}</b>\n\n"
        f"Введите ссылку на канал:\n<code>https://t.me/username</code>"
    )


@router.message(AdminState.add_mod_url)
async def handle_add_mod_url(message: Message, state: FSMContext, mod_repo: ModChannelRepo) -> None:
    if not is_admin(message.from_user.id):
        return
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("⚠️ Введите корректную ссылку начиная с https://")
        return
    data = await state.get_data()
    await mod_repo.add(
        username=data["mod_username"],
        title=data["mod_title"],
        url=url,
        is_private=data.get("mod_is_private", False),
        channel_id=data.get("mod_channel_id")
    )
    await state.clear()
    channels = await mod_repo.get_all()
    channel_type = "🔒 Приватный" if data.get("mod_is_private") else "🌐 Публичный"
    await message.answer(
        f"✅ <b>Мод-канал добавлен!</b>\n\n"
        f"🎮 {data['mod_title']}\n"
        f"Тип: {channel_type}\n"
        f"Всего каналов: <b>{len(channels)}</b>",
        reply_markup=admin_menu_keyboard()
    )


@router.callback_query(lambda c: c.data and c.data.startswith("admin_del_mod:"))
async def handle_del_mod(callback: CallbackQuery, mod_repo: ModChannelRepo) -> None:
    if not is_admin(callback.from_user.id):
        return
    channel_id = int(callback.data.split(":")[1])
    await mod_repo.remove(channel_id)
    channels = await mod_repo.get_all()
    await callback.answer("✅ Мод-канал удалён")
    text = f"🎮 <b>Мод-каналы</b>\n\nТекущих каналов: <b>{len(channels)}</b>\n\n"
    if channels:
        for ch in channels:
            lock = "🔒 Приватный" if ch.is_private else "🌐 Публичный"
            text += f"• {ch.title} — {lock}\n"
    else:
        text += "⚠️ Каналов нет."
    await callback.message.edit_text(text, reply_markup=mod_channels_keyboard(channels))


# ─── Массовая рассылка ────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "admin_broadcast")
async def handle_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminState.broadcast_text)
    await callback.answer()
    await callback.message.edit_text(
        "📨 <b>Массовая рассылка</b>\n\n"
        "Введите текст сообщения которое получат все пользователи.\n\n"
        "Поддерживается HTML:\n"
        "<code>&lt;b&gt;жирный&lt;/b&gt;</code>\n"
        "<code>&lt;i&gt;курсив&lt;/i&gt;</code>\n\n"
        "Для отмены напишите /cancel"
    )


@router.message(AdminState.broadcast_text)
async def handle_broadcast_text(
    message: Message,
    state: FSMContext,
    user_repo: UserRepo
) -> None:
    if not is_admin(message.from_user.id):
        return
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Рассылка отменена.", reply_markup=admin_menu_keyboard())
        return
    text = message.text.strip()
    all_users = await user_repo.get_all()
    user_ids = [u.telegram_id for u in all_users]
    await message.answer(f"📨 Начинаю рассылку для <b>{len(user_ids)}</b> пользователей...")
    from core.bot import bot
    success, failed = await broadcast(bot, user_ids, text)
    await state.clear()
    await message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📬 Доставлено: <b>{success}</b>\n"
        f"❌ Ошибок: <b>{failed}</b>",
        reply_markup=admin_menu_keyboard()
    )