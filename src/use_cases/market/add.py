import logging
from src.domain.entities.market import MarketDTO, MarketCondition
from src.domain.protocols.repositories.market import MarketRepository
from src.domain.protocols.polymarket import PolymarketAPI
from src.domain.exceptions import InvalidTargetPriceError, MarketAlreadyExistsError, TokenIdNotFoundError

# Keep pattern here for imports, though not used in logic anymore
POLYMARKET_URL_PATTERN = r"https?://(?:www\.)?polymarket\.com/event/([a-zA-Z0-9_-]+)"

logger = logging.getLogger(__name__)

class AddMarketUseCase:
    def __init__(
        self,
        market_repository: MarketRepository,
        polymarket_api: PolymarketAPI
    ):
        self.market_repository = market_repository
        self.polymarket_api = polymarket_api

    async def __call__(
        self,
        user_id: int,
        market_id: str,
        market_url: str,
        target_price: int
    ) -> MarketDTO:
        logger.info(f"Adding market. User: {user_id}, ID: {market_id}")
        
        # Validate price
        if not (0 <= target_price <= 100):
            raise InvalidTargetPriceError()
            
        # Check if market already exists for user
        existing_market = await self.market_repository.get_market_by_market_id(user_id, market_id)
        if existing_market:
            logger.info(f"Market already exists: {existing_market.id}")
            raise MarketAlreadyExistsError(existing_market.id)
            
        # Fetch market info to verify it exists and get title
        market_info = await self.polymarket_api.get_market_info(market_id)
        
        if not market_info.token_id:
            logger.error(f"No token_id found for market {market_id}")
            raise TokenIdNotFoundError(market_id)

        # Determine condition based on current price
        current_price = market_info.price * 100  # Convert 0-1 to 0-100
        condition = MarketCondition.LE
        
        if target_price > current_price:
            condition = MarketCondition.GE
            logger.info(f"Target {target_price} > Current {current_price}: Setting condition to GE (>=)")
        else:
            condition = MarketCondition.LE
            logger.info(f"Target {target_price} <= Current {current_price}: Setting condition to LE (<=)")
        
        # Use provided market URL (event URL)
        final_url = market_url
        
        # Create market
        market = MarketDTO(
            id=None,
            user_id=user_id,
            market_id=market_id,
            token_id=market_info.token_id,
            url=final_url,
            title=market_info.title,
            target_price=target_price,
            condition=condition,
            is_active=True,
            created_at=None
        )
        
        return await self.market_repository.create_market(market)
