from typing import Protocol

from src.domain.entities.market import MarketInfoDTO, MarketOptionDTO


class PolymarketAPI(Protocol):
    async def get_market_info(self, market_id: str) -> MarketInfoDTO:
        ...

    async def get_event_markets(self, slug: str) -> list[MarketOptionDTO]:
        ...
