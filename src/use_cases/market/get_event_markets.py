from src.domain.entities.market import MarketOptionDTO
from src.domain.protocols.polymarket import PolymarketAPI

class GetEventMarketsUseCase:
    def __init__(self, polymarket_api: PolymarketAPI):
        self.api = polymarket_api

    async def __call__(self, slug: str) -> list[MarketOptionDTO]:
        return await self.api.get_event_markets(slug)

