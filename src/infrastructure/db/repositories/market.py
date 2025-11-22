import logging
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.market import MarketDTO, MarketCondition
from src.domain.protocols.repositories.market import MarketRepository
from src.infrastructure.db.models.market import Market

logger = logging.getLogger(__name__)


class SQLAlchemyMarketRepository(MarketRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_dto(self, market: Market) -> MarketDTO:
        return MarketDTO(
            id=market.id,
            user_id=market.user_id,
            market_id=market.market_id,
            token_id=market.token_id,
            url=market.market_url,
            title=market.market_title,
            target_price=market.target_price,
            condition=market.condition,
            is_active=market.is_active,
            created_at=market.created_at,
        )

    async def create_market(self, market: MarketDTO) -> MarketDTO:
        db_market = Market(
            user_id=market.user_id,
            market_id=market.market_id,
            token_id=market.token_id,
            market_url=market.url,
            market_title=market.title,
            target_price=market.target_price,
            condition=market.condition,
            is_active=market.is_active
        )
        self.session.add(db_market)
        await self.session.commit()
        await self.session.refresh(db_market)
        return self._to_dto(db_market)

    async def get_market_by_id(self, market_id: int) -> MarketDTO | None:
        stmt = select(Market).where(Market.id == market_id)
        result = await self.session.execute(stmt)
        market = result.scalar_one_or_none()
        if market:
            return self._to_dto(market)
        return None

    async def get_markets_by_user(self, user_id: int) -> list[MarketDTO]:
        stmt = select(Market).where(Market.user_id == user_id).order_by(Market.created_at.desc())
        result = await self.session.execute(stmt)
        markets = result.scalars().all()
        return [self._to_dto(m) for m in markets]

    async def get_market_by_market_id(self, user_id: int, market_id: str) -> MarketDTO | None:
        logger.info(f"Checking DB for market. User: {user_id}, ID: '{market_id}'")
        stmt = select(Market).where(Market.user_id == user_id, Market.market_id == market_id)
        result = await self.session.execute(stmt)
        # Use first() to handle potential duplicates safely (e.g. checking existence)
        market = result.scalars().first()
        if market:
            logger.info(f"Found existing market in DB: {market.id} (ID: {market.market_id})")
            return self._to_dto(market)
        logger.info("No existing market found in DB.")
        return None

    async def update_target_price(self, market_id: int, target_price: int, condition: MarketCondition) -> MarketDTO | None:
        stmt = (
            update(Market)
            .where(Market.id == market_id)
            .values(target_price=target_price, condition=condition)
            .returning(Market)
        )
        result = await self.session.execute(stmt)
        market = result.scalar_one_or_none()
        await self.session.commit()
        if market:
            return self._to_dto(market)
        return None

    async def delete_market(self, market_id: int) -> None:
        stmt = delete(Market).where(Market.id == market_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_active_markets(self) -> list[MarketDTO]:
        stmt = select(Market).where(Market.is_active == True)
        result = await self.session.execute(stmt)
        markets = result.scalars().all()
        return [self._to_dto(m) for m in markets]

    async def update_market_status(self, market_id: int, is_active: bool) -> MarketDTO | None:
        stmt = (
            update(Market)
            .where(Market.id == market_id)
            .values(is_active=is_active)
            .returning(Market)
        )
        result = await self.session.execute(stmt)
        market = result.scalar_one_or_none()
        await self.session.commit()
        if market:
            return self._to_dto(market)
        return None
