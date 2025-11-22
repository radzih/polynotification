import asyncio
import logging
from typing import List

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.domain.entities.market import MarketDTO, MarketCondition
from src.infrastructure.db.repositories.market import SQLAlchemyMarketRepository
from src.infrastructure.polymarket.client import PolymarketApiClient

logger = logging.getLogger(__name__)

class MarketMonitorService:
    def __init__(
        self,
        session_maker: async_sessionmaker,
        polymarket_api: PolymarketApiClient,
        bot: Bot,
        scheduler: AsyncIOScheduler,
    ):
        self.session_maker = session_maker
        self.polymarket_api = polymarket_api
        self.bot = bot
        self.scheduler = scheduler

    async def start(self):
        self.scheduler.add_job(self.check_markets, "interval", seconds=5)
        self.scheduler.start()

    async def check_markets(self):
        logger.info("Checking markets...")
        
        async with self.session_maker() as session:
            market_repo = SQLAlchemyMarketRepository(session)
            active_markets = await market_repo.get_active_markets()
            
            if not active_markets:
                return

            # Group markets by token_id for batch processing
            # Since we enforce token_id, we can skip any (legacy) records that might still miss it
            # or treat them as error cases, but relying on batch API.
            markets_with_token = [m for m in active_markets if m.token_id]
            
            if len(markets_with_token) < len(active_markets):
                logger.warning(f"Found {len(active_markets) - len(markets_with_token)} active markets without token_id. Skipping them.")
            
            if not markets_with_token:
                return

            unique_tokens = list({m.token_id for m in markets_with_token})
            logger.info(f"Fetching prices for {len(unique_tokens)} tokens (Batch)")
            
            # Split into chunks of 20
            chunk_size = 20
            for i in range(0, len(unique_tokens), chunk_size):
                chunk_tokens = unique_tokens[i:i + chunk_size]
                
                try:
                    prices = await self.polymarket_api.get_prices_batch(chunk_tokens)
                    
                    for market in markets_with_token:
                        if market.token_id in chunk_tokens:
                            if market.token_id in prices:
                                current_price = prices[market.token_id] * 100
                                await self._check_and_notify(market, current_price, market_repo)
                            else:
                                # This might happen if API didn't return price for valid token
                                pass 
                except Exception as e:
                    logger.error(f"Error processing batch: {e}")

    async def _check_and_notify(self, market: MarketDTO, current_price: float, market_repo: SQLAlchemyMarketRepository):
        logger.debug(f"Checking market {market.id} ({market.market_id}): current_price={current_price}%, target={market.target_price}%, condition={market.condition}")
        should_notify = False
        
        if market.condition == MarketCondition.LE and current_price <= market.target_price:
            should_notify = True
            logger.info(f"Market {market.id} triggered (LE): {current_price}% <= {market.target_price}%")
        elif market.condition == MarketCondition.GE and current_price >= market.target_price:
            should_notify = True
            logger.info(f"Market {market.id} triggered (GE): {current_price}% >= {market.target_price}%")
            
        if should_notify:
            await self.notify_and_disable(market, current_price, market_repo)

    async def notify_and_disable(self, market: MarketDTO, current_price: float, market_repo: SQLAlchemyMarketRepository):
        logger.info(f"Market {market.id} triggered! Price: {current_price}, Target: {market.target_price}")
        
        # Disable monitoring
        await market_repo.update_market_status(market.id, is_active=False)
        
        # Send notification
        text = (
            f"🚨 <b>Market Alert!</b>\n\n"
            f"📉 <b>{market.title or market.market_id}</b>\n"
            f"Current Price: {current_price:.2f}%\n"
            f"Target: {market.target_price}%\n\n"
            f"Monitoring has been disabled."
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 View on Polymarket", url=market.url)],
            [InlineKeyboardButton(text="🔄 Re-enable Monitoring", callback_data=f"enable_mon:{market.id}")]
        ])
        
        try:
            await self.bot.send_message(market.user_id, text, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Failed to send notification to {market.user_id}: {e}")
