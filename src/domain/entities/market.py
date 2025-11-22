from dataclasses import dataclass
from datetime import datetime
import enum

class MarketCondition(str, enum.Enum):
    LE = "le"  # Less or Equal
    GE = "ge"  # Greater or Equal

@dataclass
class MarketDTO:
    id: int | None
    user_id: int
    market_id: str
    token_id: str
    url: str
    title: str | None
    target_price: int  # 0-100
    condition: MarketCondition
    is_active: bool
    created_at: datetime | None

    @property
    def status_icon(self) -> str:
        return "✅" if self.is_active else "⏸️"

@dataclass
class MarketInfoDTO:
    title: str
    price: float  # 0.0-1.0
    market_id: str
    token_id: str | None = None
    slug: str | None = None

@dataclass
class MarketOptionDTO:
    id: str
    question: str
    active: bool
