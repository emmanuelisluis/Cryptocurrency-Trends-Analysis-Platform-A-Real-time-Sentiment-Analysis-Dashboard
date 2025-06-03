"""
Pydantic models for Trade related API requests and responses.
"""
from datetime import datetime
from typing import List, Optional # List was already imported but good to be explicit

from pydantic import BaseModel, Field

class TradeAPIResponse(BaseModel):
    """
    API response model for a single trade.
    Reflects the structure of data served by the /trades endpoint.
    """
    timestamp: datetime = Field(..., description="Timestamp of the trade execution (UTC).")
    symbol: str = Field(..., description="Trading symbol (e.g., 'btcusdt').")
    exchange: str = Field(..., description="Exchange name (e.g., 'binance').")
    price: float = Field(..., description="Execution price of the trade.")
    volume: float = Field(..., description="Volume/quantity of the trade in base asset.")
    side: str = Field(..., description="Side of the taker order ('buy' or 'sell').")
    trade_id: str = Field(..., description="Unique trade ID from the exchange.")
    aggressor_side: Optional[str] = Field(None, description="The side that initiated the trade (aggressor), 'buy' or 'sell'. Null if not available or unknown. This is derived from the 'm' (isBuyerMaker) flag from Binance raw trades during ingestion.")
    # Consider adding `isBuyerMaker: Optional[bool]` if frontend needs the raw flag. For now, `aggressor_side` is more direct.


    class Config:
        from_attributes = True # Pydantic V2 for ORM mode (enables creating from ORM objects)

class TradesAPIRequestParams(BaseModel):
    """
    Pydantic model for validating query parameters for the recent trades API endpoint.
    """
    limit: int = Field(
        default=100,
        ge=1,
        le=1000, # Max limit can be adjusted based on performance considerations
        description="Number of recent trades to fetch. Maximum 1000."
    )
    since_timestamp_utc: Optional[datetime] = Field( # Changed from str to datetime for auto-conversion by FastAPI
        default=None,
        description="Fetch trades since this UTC timestamp (ISO 8601 format, e.g., YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS). If timezone info is missing, UTC is assumed.",
        examples=["2023-10-27T10:00:00Z", "2023-10-27T10:00:00"]
    )
    min_volume: Optional[float] = Field(
        default=None,
        ge=0,
        description="Minimum trade volume (in base currency quantity) to filter by. If 0, no filter is applied."
    )

    # Note on since_timestamp_utc:
    # FastAPI/Pydantic will attempt to parse ISO 8601 strings into datetime objects.
    # If the string includes 'Z' or a timezone offset (+HH:MM), it will be timezone-aware.
    # If no timezone info is provided, Pydantic/FastAPI might treat it as naive.
    # It's crucial that the service layer ensures these are handled as UTC.
    # The service currently uses `datetime.fromisoformat(str.replace('Z', '+00:00'))` if it's a string,
    # which is robust. If Pydantic converts to datetime directly, ensure it handles tz correctly.
