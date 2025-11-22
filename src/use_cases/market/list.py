from src.domain.entities.market import MarketDTO
from src.domain.protocols.repositories.market import MarketRepository


class ListUserMarketsUseCase:
    def __init__(self, market_repository: MarketRepository):
        self.market_repository = market_repository

    async def __call__(self, user_id: int) -> list[MarketDTO]:
        return await self.market_repository.get_markets_by_user(user_id)


