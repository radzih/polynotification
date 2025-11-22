from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.use_cases.user.create import CreateUserUseCase

router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    create_user_use_case: CreateUserUseCase
):
    await create_user_use_case(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    
    await message.answer("Hello! You have been registered in the database.")
