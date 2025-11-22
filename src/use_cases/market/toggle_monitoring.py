from src.domain.entities.market import MarketDTO
from src.domain.protocols.repositories.market import MarketRepository


class ToggleMonitoringUseCase:
    def __init__(self, market_repository: MarketRepository):
        self.market_repository = market_repository

    async def __call__(self, market_id: int, is_active: bool) -> MarketDTO | None:
        return await self.market_repository.update_market_status(market_id, is_active=is_active)

