"""
Pydantic models for representing standardized exchange data.

These models are used primarily by the data ingestion services (e.g., BinanceWebSocketClient)
to structure data parsed from WebSocket streams before it's passed to handlers
(like the database writer). They ensure data consistency and type safety.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

class TradeData(BaseModel):
    """
    Represents a single trade event from an exchange, normalized.
    This model is used for internal data transfer after parsing from WebSocket.
    """
    timestamp: datetime = Field(..., description="Timestamp of the trade execution (UTC).")
    price: float = Field(..., description="Execution price of the trade.")
    volume: float = Field(..., description="Volume/quantity of the trade in base asset.")
    side: str = Field(..., description="Side of the taker order ('buy' or 'sell').") # This is Taker's side
    exchange: str = Field(..., description="Name of the exchange where the trade occurred.")
    symbol: str = Field(..., description="Trading symbol (e.g., 'btcusdt').")
    trade_id: str = Field(..., description="Unique trade ID from the exchange.")
    aggressor_side: Optional[str] = Field(None, description="The side that initiated the trade (aggressor), 'buy' or 'sell'. Null if unknown.")

    class Config:
        from_attributes = True # Useful if ever constructed from ORM objects, though primarily for raw data


class OrderBookLevel(BaseModel):
    """
    Represents a single price level in an order book (either a bid or an ask).
    """
    price: float = Field(..., description="Price for this order book level.")
    volume: float = Field(..., description="Total volume/quantity available at this price level.")

    class Config:
        from_attributes = True


class OrderBookData(BaseModel):
    """
    Represents a snapshot or update of an order book for a symbol.
    This model is used for internal data transfer after parsing from WebSocket.
    """
    timestamp: datetime = Field(..., description="Timestamp of the order book data (UTC).")
    symbol: str = Field(..., description="Trading symbol.")
    exchange: str = Field(..., description="Name of the exchange.")
    bids: List[OrderBookLevel] = Field(..., description="List of bid levels, typically sorted highest price first.")
    asks: List[OrderBookLevel] = Field(..., description="List of ask levels, typically sorted lowest price first.")
    last_update_id: Optional[int] = Field(None, description="For exchanges like Binance, the last update ID of the event(s) in this snapshot/update.")

    class Config:
        from_attributes = True


class TickerData(BaseModel):
    """
    Represents ticker data (price summary) for a symbol from an exchange.
    This model is used for internal data transfer after parsing from WebSocket.
    """
    timestamp: datetime = Field(..., description="Timestamp of the ticker data (UTC).")
    symbol: str = Field(..., description="Trading symbol.")
    exchange: str = Field(..., description="Name of the exchange.")
    last_price: float = Field(..., description="Last traded price.")
    volume_24h: Optional[float] = Field(None, description="Total traded base asset volume in the last 24 hours.")
    high_24h: Optional[float] = Field(None, description="Highest price in the last 24 hours.")
    low_24h: Optional[float] = Field(None, description="Lowest price in the last 24 hours.")
    price_change_percent_24h: Optional[float] = Field(None, description="Price change percentage in the last 24 hours.")

    class Config:
        from_attributes = True

# Note: `from_attributes = True` (Pydantic V2) or `orm_mode = True` (Pydantic V1)
# allows Pydantic models to be created from ORM objects (SQLAlchemy models) by attribute access.
# While these specific models are primarily for raw data parsing, it's a good default.
