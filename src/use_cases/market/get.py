from src.domain.entities.market import MarketDTO
from src.domain.protocols.repositories.market import MarketRepository
from src.domain.exceptions import MarketNotFoundError


class GetMarketUseCase:
    def __init__(self, market_repository: MarketRepository):
        self.market_repository = market_repository

    async def __call__(self, market_id: int) -> MarketDTO:
        market = await self.market_repository.get_market_by_id(market_id)
        if not market:
            raise MarketNotFoundError(market_id)
        return market


