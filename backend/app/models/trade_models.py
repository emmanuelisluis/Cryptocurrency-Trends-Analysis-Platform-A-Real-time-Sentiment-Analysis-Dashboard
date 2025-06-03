from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TradeAPIResponse(BaseModel):
    timestamp: datetime
    symbol: str
    exchange: str
    price: float
    volume: float
    side: str # 'buy' or 'sell'
    trade_id: str
    # aggressor_side: Optional[str] = None # 'buy' or 'sell', indicating which side was the aggressor
                                       # This requires isBuyerMaker (or similar) to be stored during ingestion.

    class Config:
        from_attributes = True # Pydantic V2 for ORM mode

class TradesAPIRequestParams(BaseModel): # For query parameters
    limit: int = Field(default=100, ge=1, le=1000, description="Number of recent trades to fetch. Max 1000.") # Increased max limit
    # Using strings for timestamps that will be converted by FastAPI/Pydantic
    # This avoids issues with URL encoding of datetime objects directly.
    # FastAPI will handle parsing to datetime based on type hint in service/endpoint.
    since_timestamp_utc: Optional[str] = Field(
        default=None,
        description="Fetch trades since this UTC timestamp (ISO 8601 format, e.g., YYYY-MM-DDTHH:MM:SSZ)",
        examples=["2023-01-01T00:00:00Z"]
    )
    min_volume: Optional[float] = Field(
        default=None,
        ge=0,
        description="Minimum trade volume (in base currency quantity) to filter by"
    )
