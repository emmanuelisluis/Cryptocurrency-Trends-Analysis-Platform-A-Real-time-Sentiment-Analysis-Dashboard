from pydantic import BaseModel, Field
from typing import List, Dict, Optional # Dict not used in these specific models but good to have for Pydantic
from datetime import datetime

class FootprintPriceLevel(BaseModel):
    price: float
    bid_volume: float = 0.0  # Volume from trades where seller was aggressor
    ask_volume: float = 0.0  # Volume from trades where buyer was aggressor
    delta: float = 0.0       # Calculated as ask_volume - bid_volume
    total_volume: float = 0.0 # Calculated as bid_volume + ask_volume

    class Config:
        from_attributes = True

class FootprintBar(BaseModel):
    timestamp: datetime  # Start time of the bar/candle (UTC)
    open: float
    high: float
    low: float
    close: float
    total_volume: float  # Total volume for the entire bar (sum of price_levels' total_volume)
    total_delta: float   # Total delta for the entire bar (sum of price_levels' delta)
    price_levels: List[FootprintPriceLevel] = Field(default_factory=list) # Sorted by price ascending

    # Optional fields for more advanced footprint features
    # point_of_control_price: Optional[float] = None
    # value_area_high_price: Optional[float] = None
    # value_area_low_price: Optional[float] = None

    class Config:
        from_attributes = True

class FootprintChartDataResponse(BaseModel):
    exchange: str
    symbol: str
    timeframe: str # e.g., "1m", "5m", "1H"
    bars: List[FootprintBar]

    class Config:
        from_attributes = True
