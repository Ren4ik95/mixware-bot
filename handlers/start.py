from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        f"Привет, <b>{message.from_user.full_name}</b>! 👋\n\n"
        "Используй меню ниже для навигации."
    )