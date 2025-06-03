"""
Pydantic models for Footprint Chart related API responses.

These models define the structure for footprint bars, including the detailed
bid/ask volume at each price level within a bar, OHLC, total volume, and total delta.
"""
from datetime import datetime
from typing import List, Optional # Dict was unused, removed

from pydantic import BaseModel, Field


class FootprintPriceLevel(BaseModel):
    """
    Represents aggregated bid and ask volume at a specific price level
    within a single footprint bar.
    """
    price: float = Field(..., description="Price level.")
    bid_volume: float = Field(default=0.0, description="Total volume of trades where sellers were aggressors (hit the bid).")
    ask_volume: float = Field(default=0.0, description="Total volume of trades where buyers were aggressors (hit the ask).")
    delta: float = Field(default=0.0, description="Difference between ask volume and bid volume (ask_volume - bid_volume).")
    total_volume: float = Field(default=0.0, description="Total volume traded at this price level (bid_volume + ask_volume).")

    class Config:
        from_attributes = True


class FootprintBar(BaseModel):
    """
    Represents a single bar in a footprint chart, containing OHLC data,
    total volume, total delta, and a list of price level details.
    """
    timestamp: datetime = Field(..., description="Start timestamp of the bar/candle (UTC).")
    open: float = Field(..., description="Opening price of the bar.")
    high: float = Field(..., description="Highest price of the bar.")
    low: float = Field(..., description="Lowest price of the bar.")
    close: float = Field(..., description="Closing price of the bar.")
    total_volume: float = Field(..., description="Total volume traded within this bar (sum of all price_levels' total_volume).")
    total_delta: float = Field(..., description="Total delta for this bar (sum of all price_levels' delta).")
    price_levels: List[FootprintPriceLevel] = Field(default_factory=list, description="Detailed bid/ask volume at each price level within the bar, sorted by price ascending.")

    # Optional advanced features that could be added later:
    # point_of_control_price: Optional[float] = Field(None, description="Price level with the highest total_volume in this bar.")
    # value_area_high_price: Optional[float] = Field(None, description="Highest price of the value area (e.g., 70% of volume).")
    # value_area_low_price: Optional[float] = Field(None, description="Lowest price of the value area.")

    class Config:
        from_attributes = True


class FootprintChartDataResponse(BaseModel):
    """
    API response model for footprint chart data.
    Contains metadata and a list of footprint bars.
    """
    exchange: str = Field(..., description="Exchange name.")
    symbol: str = Field(..., description="Trading symbol.")
    timeframe: str = Field(..., description="Timeframe of the bars (e.g., '1m', '5m', '1H').")
    bars: List[FootprintBar] = Field(..., description="List of footprint bars for the requested period.")

    class Config:
        from_attributes = True
