from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from fluentogram import TranslatorRunner

from src.use_cases.user.create import CreateUserUseCase

router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    create_user_use_case: CreateUserUseCase,
    i18n: TranslatorRunner,
):
    await create_user_use_case(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    
    await message.answer(i18n.start_welcome())
    await message.answer(i18n.add_market_prompt_url())
