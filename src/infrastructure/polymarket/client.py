import aiohttp
import json
import logging
from typing import Optional

from src.domain.entities.market import MarketInfoDTO, MarketOptionDTO
from src.domain.protocols.polymarket import PolymarketAPI
from src.domain.exceptions import MarketNotFoundError, MarketApiError

logger = logging.getLogger(__name__)


class PolymarketApiClient(PolymarketAPI):
    BASE_URL = "https://gamma-api.polymarket.com"
    CLOB_API_URL = "https://clob.polymarket.com"

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self._session = session
        self._owns_session = False

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self):
        if self._owns_session and self._session:
            await self._session.close()
            self._session = None

    async def get_event_markets(self, slug: str) -> list[MarketOptionDTO]:
        session = await self._get_session()
        url = f"{self.BASE_URL}/events"
        params = {"slug": slug}
        
        try:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise MarketApiError(f"Failed to fetch event: {response.status}")
                
                data = await response.json()
                
                if not data:
                    raise MarketNotFoundError(slug)
                
                event = data[0]
                markets_data = event.get("markets", [])
                
                return [
                    MarketOptionDTO(
                        id=m["id"], 
                        question=m.get("question", "Unknown Question"),
                        active=m.get("active", True)
                    ) 
                    for m in markets_data
                    if m.get("closed") is False
                ]
        except aiohttp.ClientError as e:
            raise MarketApiError(f"Network error: {str(e)}")

    async def get_market_info(self, market_id: str) -> MarketInfoDTO:
        # Fetch by Market ID directly
        session = await self._get_session()
        url = f"{self.BASE_URL}/markets/{market_id}"
        
        try:
            logger.debug(f"Fetching market info for {market_id} from {url}")
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch market info for {market_id}: HTTP {response.status}")
                    raise MarketApiError(f"Failed to fetch market info: {response.status}")
                
                data = await response.json()
                logger.debug(f"API response for {market_id} - json: {data}")
                
                title = data.get("question", "Unknown Market")
                slug = data.get("slug")
                
                # Extract token_id
                token_id = None
                clob_token_ids = data.get("clobTokenIds", [])
                if isinstance(clob_token_ids, str):
                    try:
                        clob_token_ids = json.loads(clob_token_ids)
                    except json.JSONDecodeError:
                        clob_token_ids = []
                
                if isinstance(clob_token_ids, list) and len(clob_token_ids) > 0:
                    token_id = clob_token_ids[0]
                
                current_price = 0.0
                
                # First priority: use bestBid price
                if "bestAsk" in data and data["bestAsk"] is not None:
                    try:
                        current_price = float(data["bestAsk"])
                        logger.debug(f"Using bestAsk for {market_id}: {current_price}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not parse bestAsk for {market_id}: {data.get('bestAsk')}, error: {e}")
                
                # Fallback: try outcomePrices array (assuming first is Yes)
                if current_price == 0.0:
                    outcome_prices = data.get("outcomePrices", [])
                    logger.debug(f"outcomePrices for {market_id}: {outcome_prices}")
                    
                    if outcome_prices:
                        try:
                            # Handle case where outcomePrices might be a JSON string
                            if isinstance(outcome_prices, str):
                                outcome_prices = json.loads(outcome_prices)
                            
                            if isinstance(outcome_prices, list) and len(outcome_prices) > 0:
                                current_price = float(outcome_prices[0])
                                logger.debug(f"Using outcomePrices[0] for {market_id}: {current_price}")
                        except (ValueError, IndexError, TypeError, json.JSONDecodeError) as e:
                            logger.error(f"Error parsing outcomePrices for {market_id}: {e}, outcomePrices={outcome_prices}")
                
                # Fallback: try to find the "Yes" outcome from the outcomes array
                if current_price == 0.0:
                    outcomes = data.get("outcomes", [])
                    logger.debug(f"outcomes for {market_id}: {outcomes}")
                    
                    if outcomes:
                        # Handle case where outcomes might be a JSON string
                        if isinstance(outcomes, str):
                            try:
                                outcomes = json.loads(outcomes)
                            except json.JSONDecodeError:
                                logger.warning(f"Could not parse outcomes JSON string for {market_id}")
                                outcomes = []
                        
                        if isinstance(outcomes, list):
                            # Look for the "Yes" outcome
                            yes_outcome = None
                            for outcome in outcomes:
                                if isinstance(outcome, dict):
                                    outcome_name = outcome.get("name", "").lower()
                                    logger.debug(f"Checking outcome: {outcome}, name: {outcome_name}")
                                    if "yes" in outcome_name:
                                        yes_outcome = outcome
                                        break
                                elif isinstance(outcome, str) and "yes" in outcome.lower():
                                    yes_outcome = outcome
                                    break
                            
                            if yes_outcome:
                                # Extract price from Yes outcome
                                if isinstance(yes_outcome, dict):
                                    # Try different possible price fields
                                    price = yes_outcome.get("price") or yes_outcome.get("currentPrice") or yes_outcome.get("lastPrice")
                                    if price is not None:
                                        try:
                                            current_price = float(price)
                                            logger.debug(f"Found Yes outcome price for {market_id}: {current_price}")
                                        except (ValueError, TypeError):
                                            logger.warning(f"Could not parse Yes outcome price for {market_id}: {price}")
                
                # Fallback: try direct price fields
                if current_price == 0.0:
                    logger.debug(f"Checking alternative price fields for {market_id}")
                    
                    # Check common alternative fields
                    if "yesPrice" in data:
                        try:
                            current_price = float(data["yesPrice"])
                            logger.debug(f"Found 'yesPrice' field for {market_id}: {current_price}")
                        except (ValueError, TypeError):
                            logger.warning(f"Could not parse yesPrice for {market_id}: {data.get('yesPrice')}")
                    elif "currentPrice" in data:
                        try:
                            current_price = float(data["currentPrice"])
                            logger.debug(f"Found 'currentPrice' field for {market_id}: {current_price}")
                        except (ValueError, TypeError):
                            logger.warning(f"Could not parse currentPrice for {market_id}: {data.get('currentPrice')}")
                    elif "lastTradePrice" in data:
                        try:
                            current_price = float(data["lastTradePrice"])
                            logger.debug(f"Found 'lastTradePrice' field for {market_id}: {current_price}")
                        except (ValueError, TypeError):
                            logger.warning(f"Could not parse lastTradePrice for {market_id}: {data.get('lastTradePrice')}")
                
                if current_price == 0.0:
                    logger.warning(f"Could not find price for {market_id}, defaulting to 0.0")

                logger.info(f"Market {market_id} ({title}): price={current_price}")
                return MarketInfoDTO(
                    title=title,
                    price=current_price,
                    market_id=market_id,
                    slug=slug,
                    token_id=token_id
                )
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching market {market_id}: {e}")
            raise MarketApiError(f"Network error: {str(e)}")

    async def get_prices_batch(self, token_ids: list[str]) -> dict[str, float]:
        """
        Fetch prices for multiple tokens in a single batch request.
        Returns a dictionary mapping token_id to price.
        """
        if not token_ids:
            return {}

        session = await self._get_session()
        url = f"{self.CLOB_API_URL}/prices"
        
        # We request "SELL" side to get the Ask price (what we would pay to buy "Yes")
        # Matches logic in get_market_info which uses bestAsk
        payload = [{"token_id": tid, "side": "SELL"} for tid in token_ids]
        
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch batch prices: HTTP {response.status}")
                    # Return empty dict on failure, or could raise error
                    return {}
                
                data = await response.json()
                # Data structure:
                # { "token_id_1": { "BUY": "...", "SELL": "..." }, ... }
                
                prices = {}
                for tid, price_data in data.items():
                    try:
                        # We requested SELL side, so look for SELL price
                        sell_price = price_data.get("SELL")
                        if sell_price:
                            prices[tid] = float(sell_price)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse price for token {tid}: {price_data}")
                
                return prices
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching batch prices: {e}")
            return {}
