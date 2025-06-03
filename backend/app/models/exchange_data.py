from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class TradeData(BaseModel):
    timestamp: datetime
    price: float
    volume: float
    side: str  # 'buy' or 'sell'
    exchange: str
    symbol: str
    trade_id: str # Ensure this is populated, e.g., from Binance 't' field
    aggressor_side: Optional[str] = None # 'buy' or 'sell', indicates the taker side

class OrderBookLevel(BaseModel):
    price: float
    volume: float

class OrderBookData(BaseModel):
    timestamp: datetime
    symbol: str
    exchange: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    last_update_id: Optional[int] = None

class TickerData(BaseModel):
    timestamp: datetime
    symbol: str
    exchange: str
    last_price: float
    volume_24h: float
    high_24h: float
    low_24h: float
    price_change_percent_24h: float

# Ensure __init__.py exists for the models directory
# (already created in the previous subtask, but good to keep in mind)
