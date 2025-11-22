import asyncio
import logging

from aiogram import Bot, Dispatcher

from src.bootstrap.config import get_settings
from src.bootstrap.database import create_engine_factory, create_session_maker
from src.presentation.handlers.start import router as start_router
from src.presentation.middlewares.db import DbSessionMiddleware
from src.presentation.middlewares.use_cases import UseCaseMiddleware


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    settings = get_settings()
    
    # Database setup
    engine = create_engine_factory()
    session_maker = create_session_maker(engine)
    
    # Bot setup
    bot = Bot(token=settings.bot_token.get_secret_value())
    dp = Dispatcher()
    
    # Middleware
    dp.update.middleware(DbSessionMiddleware(session_maker))
    dp.update.middleware(UseCaseMiddleware())
    
    # Register routers
    dp.include_router(start_router)

    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
