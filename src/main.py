import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram_dialog import setup_dialogs
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.bootstrap.config import get_settings
from src.bootstrap.database import create_engine_factory, create_session_maker
from src.infrastructure.polymarket.client import PolymarketApiClient
from src.infrastructure.scheduler.monitoring import MarketMonitorService
from src.presentation.handlers.start import router as start_router
from src.presentation.handlers.market import router as market_router
from src.presentation.handlers.errors import router as errors_router
from src.presentation.dialogs.add_market import add_market_dialog
from src.presentation.dialogs.market_list import market_list_dialog
from src.presentation.middlewares.db import DbSessionMiddleware
from src.presentation.middlewares.use_cases import UseCaseMiddleware


async def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    settings = get_settings()
    
    # Database setup
    engine = create_engine_factory()
    session_maker = create_session_maker(engine)
    
    # API Client setup
    polymarket_api = PolymarketApiClient()
    
    # Bot setup
    bot = Bot(token=settings.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Middleware
    dp.update.middleware(DbSessionMiddleware(session_maker))
    dp["polymarket_api"] = polymarket_api
    dp.update.middleware(UseCaseMiddleware())
    
    # Router setup
    errors_router.include_routers(
        start_router,
        market_router,
        add_market_dialog,
        market_list_dialog
    )
    
    dp.include_router(errors_router)
    
    setup_dialogs(dp)

    # Monitoring Service
    scheduler = AsyncIOScheduler()
    monitor_service = MarketMonitorService(
        session_maker=session_maker,
        polymarket_api=polymarket_api,
        bot=bot,
        scheduler=scheduler
    )
    
    await monitor_service.start()
    
    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        await polymarket_api.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
