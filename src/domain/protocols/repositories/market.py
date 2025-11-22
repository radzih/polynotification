from typing import Protocol

from src.domain.entities.market import MarketDTO, MarketCondition


class MarketRepository(Protocol):
    async def create_market(self, market: MarketDTO) -> MarketDTO:
        ...

    async def get_market_by_id(self, market_id: int) -> MarketDTO | None:
        ...

    async def get_markets_by_user(self, user_id: int) -> list[MarketDTO]:
        ...
        
    async def get_market_by_market_id(self, user_id: int, market_id: str) -> MarketDTO | None:
        ...

    async def update_target_price(self, market_id: int, target_price: int, condition: MarketCondition) -> MarketDTO | None:
        ...

    async def delete_market(self, market_id: int) -> None:
        ...

    async def get_active_markets(self) -> list[MarketDTO]:
        ...

    async def update_market_status(self, market_id: int, is_active: bool) -> MarketDTO | None:
        ...
