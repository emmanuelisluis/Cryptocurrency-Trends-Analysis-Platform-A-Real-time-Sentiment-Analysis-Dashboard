"""
Pydantic models for Volume Profile related API responses.

These models define the structure for volume profile data, including individual
price levels with their total volume, and overall profile metrics like POC and Value Area.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class VolumeProfileLevel(BaseModel):
    """
    Represents a single price level within a volume profile, showing total volume traded.
    """
    price: float = Field(..., description="Price level.")
    total_volume: float = Field(..., description="Total volume traded at this price level.")

    class Config:
        from_attributes = True


class VolumeProfileData(BaseModel):
    """
    API response model for volume profile data.
    Includes metadata about the profile (type, time range) and the calculated profile itself.
    """
    profile_type: str = Field(..., description="Type of profile calculated (e.g., 'daily', 'range', 'weekly', 'monthly').")
    start_time_utc: datetime = Field(..., description="Start timestamp of the data range used for the profile (UTC).")
    end_time_utc: datetime = Field(..., description="End timestamp of the data range used for the profile (UTC).")

    levels: List[VolumeProfileLevel] = Field(default_factory=list, description="List of price levels and their total volumes, sorted by price ascending.")

    point_of_control_price: Optional[float] = Field(None, description="Price level with the highest traded volume (Point of Control).")
    point_of_control_volume: Optional[float] = Field(None, description="Volume traded at the Point of Control price.")

    value_area_high: Optional[float] = Field(None, description="Highest price of the Value Area (e.g., where 70% of volume was traded).")
    value_area_low: Optional[float] = Field(None, description="Lowest price of the Value Area.")

    total_profile_volume: float = Field(default=0.0, description="Total volume traded across all price levels in this profile.")

    class Config:
        from_attributes = True
