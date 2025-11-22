from src.domain.entities.market import MarketDTO
from src.domain.protocols.repositories.market import MarketRepository

class CheckMarketExistsUseCase:
    def __init__(self, market_repository: MarketRepository):
        self.market_repository = market_repository

    async def __call__(self, user_id: int, market_id: str) -> MarketDTO | None:
        # We reuse get_market_by_market_id as it queries the market_id column
        return await self.market_repository.get_market_by_market_id(user_id, market_id)
