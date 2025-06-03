from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class VolumeProfileLevel(BaseModel):
    price: float
    total_volume: float

    class Config:
        from_attributes = True

class VolumeProfileData(BaseModel):
    profile_type: str # e.g., "daily", "range", "weekly", "monthly"
    start_time_utc: datetime
    end_time_utc: datetime
    levels: List[VolumeProfileLevel] = Field(default_factory=list) # Sorted by price

    point_of_control_price: Optional[float] = None
    point_of_control_volume: Optional[float] = None # Volume at the POC price

    value_area_high: Optional[float] = None
    value_area_low: Optional[float] = None

    total_profile_volume: float = 0.0

    class Config:
        from_attributes = True
