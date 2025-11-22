from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.infrastructure.db.repositories.user import SQLAlchemyUserRepository
from src.use_cases.user.create import CreateUserUseCase


class UseCaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        session_maker: async_sessionmaker = data["session_maker"]
        
        async with session_maker() as session:
            user_repo = SQLAlchemyUserRepository(session)
            
            data["create_user_use_case"] = CreateUserUseCase(user_repo)
            
            return await handler(event, data)

