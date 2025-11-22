from src.domain.protocols.repositories.market import MarketRepository


class DeleteMarketUseCase:
    def __init__(self, market_repository: MarketRepository):
        self.market_repository = market_repository

    async def __call__(self, market_id: int) -> None:
        await self.market_repository.delete_market(market_id)


