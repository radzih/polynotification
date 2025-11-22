from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.infrastructure.db.repositories.user import SQLAlchemyUserRepository
from src.infrastructure.db.repositories.market import SQLAlchemyMarketRepository
from src.use_cases.user.create import CreateUserUseCase
from src.use_cases.market.add import AddMarketUseCase
from src.use_cases.market.list import ListUserMarketsUseCase
from src.use_cases.market.update import UpdateMarketUseCase
from src.use_cases.market.delete import DeleteMarketUseCase
from src.use_cases.market.get import GetMarketUseCase
from src.use_cases.market.check_exists import CheckMarketExistsUseCase
from src.use_cases.market.get_event_markets import GetEventMarketsUseCase
from src.use_cases.market.toggle_monitoring import ToggleMonitoringUseCase


class UseCaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        session_maker: async_sessionmaker = data["session_maker"]
        polymarket_api = data["polymarket_api"]
        
        async with session_maker() as session:
            user_repo = SQLAlchemyUserRepository(session)
            market_repo = SQLAlchemyMarketRepository(session)
            
            data["create_user_use_case"] = CreateUserUseCase(user_repo)
            
            data["add_market_use_case"] = AddMarketUseCase(market_repo, polymarket_api)
            data["list_markets_use_case"] = ListUserMarketsUseCase(market_repo)
            data["update_market_use_case"] = UpdateMarketUseCase(market_repo, polymarket_api)
            data["delete_market_use_case"] = DeleteMarketUseCase(market_repo)
            data["get_market_use_case"] = GetMarketUseCase(market_repo)
            data["check_market_exists_use_case"] = CheckMarketExistsUseCase(market_repo)
            data["get_event_markets_use_case"] = GetEventMarketsUseCase(polymarket_api)
            data["toggle_monitoring_use_case"] = ToggleMonitoringUseCase(market_repo)
            
            return await handler(event, data)
