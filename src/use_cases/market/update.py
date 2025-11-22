import logging
from src.domain.entities.market import MarketDTO, MarketCondition
from src.domain.protocols.repositories.market import MarketRepository
from src.domain.protocols.polymarket import PolymarketAPI
from src.domain.exceptions import InvalidTargetPriceError, MarketNotFoundError, MarketApiError

logger = logging.getLogger(__name__)

class UpdateMarketUseCase:
    def __init__(self, market_repository: MarketRepository, polymarket_api: PolymarketAPI):
        self.market_repository = market_repository
        self.polymarket_api = polymarket_api

    async def __call__(self, market_id: int, new_target_price: int) -> MarketDTO:
        if not (0 <= new_target_price <= 100):
            raise InvalidTargetPriceError()

        # Get existing market to get the polymarket ID
        market = await self.market_repository.get_market_by_id(market_id)
        if not market:
            raise MarketNotFoundError(market_id)

        # Fetch current market info to determine condition
        try:
            market_info = await self.polymarket_api.get_market_info(market.market_id)
            current_price = market_info.price * 100  # Convert 0-1 to 0-100
            
            condition = MarketCondition.LE
            if new_target_price > current_price:
                condition = MarketCondition.GE
                logger.info(f"Target {new_target_price} > Current {current_price}: Setting condition to GE (>=)")
            else:
                condition = MarketCondition.LE
                logger.info(f"Target {new_target_price} <= Current {current_price}: Setting condition to LE (<=)")
                
        except MarketApiError as e:
            logger.error(f"Failed to fetch market info for condition calculation: {e}")
            # If API fails, we might want to keep the old condition or fail? 
            # For now, let's keep the old condition or default to LE?
            # But wait, if we are changing target price, the old condition might be wrong.
            # If we can't check price, we can't accurately set condition.
            # Let's assume we should proceed but maybe log a warning? 
            # Or better, propagate the error because the user expects correct logic.
            # Re-raising seems appropriate as we need to set the condition correctly.
            raise

        updated_market = await self.market_repository.update_target_price(market_id, new_target_price, condition)
        if not updated_market:
            raise MarketNotFoundError(market_id)
            
        return updated_market
