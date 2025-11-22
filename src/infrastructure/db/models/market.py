from datetime import datetime
import enum

from sqlalchemy import BigInteger, String, Integer, DateTime, func, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MarketCondition(str, enum.Enum):
    LE = "le"  # Less or Equal
    GE = "ge"  # Greater or Equal


class Market(Base):
    __tablename__ = "markets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    market_id: Mapped[str] = mapped_column(String, nullable=False)
    token_id: Mapped[str | None] = mapped_column(String, nullable=True)
    market_url: Mapped[str] = mapped_column(String, nullable=False)
    market_title: Mapped[str | None] = mapped_column(String, nullable=True)
    target_price: Mapped[int] = mapped_column(Integer, nullable=False)
    condition: Mapped[MarketCondition] = mapped_column(SAEnum(MarketCondition), default=MarketCondition.LE, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
