from pydantic import BaseModel, Field
from typing import List, Optional # Added Optional
from datetime import datetime

class CVDDataPoint(BaseModel):
    timestamp: datetime # Corresponds to the end/timestamp of the bar
    cvd_value: float

    class Config:
        from_attributes = True

# Models for Advanced Delta Metrics

class ATRDataPoint(BaseModel): # For internal use or if ATR is exposed directly later
    timestamp: datetime
    atr_value: float

    class Config:
        from_attributes = True

class DVPRDataPoint(BaseModel): # Delta Volume Pressure Ratio
    timestamp: datetime # Bar timestamp
    dvpr_value: Optional[float] = Field(None, description="Delta / (Volume * ATR); can be None if ATR or Volume is zero or not calculable")
    bar_delta: float
    bar_volume: float
    bar_atr: Optional[float] = Field(None, description="ATR for that bar's period; can be None if not calculable")

    class Config:
        from_attributes = True

class DMRVDataPoint(BaseModel): # Delta Moving Average Rate of Change (or Ratio/Velocity)
    timestamp: datetime # Bar timestamp
    short_delta_ma: Optional[float] = Field(None, description="Short-term moving average of delta")
    long_delta_ma: Optional[float] = Field(None, description="Long-term moving average of delta")
    dmrv_value: Optional[float] = Field(None, description="Difference: short_delta_ma - long_delta_ma")
    # Or, if velocity (rate of change of dmrv_value):
    # dmrv_value_diff: Optional[float] = Field(None, description="Change from previous dmrv_value")

    class Config:
        from_attributes = True

class AdvancedDeltaMetricsResponse(BaseModel):
    exchange: str
    symbol: str
    timeframe: str
    dvpr_points: List[DVPRDataPoint]
    dmrv_points: List[DMRVDataPoint]

    class Config:
        from_attributes = True

class CVDChartDataResponse(BaseModel):
    exchange: str
    symbol: str
    timeframe: str # Timeframe of the underlying bars used for delta calculation
    reset_condition: str # e.g., "none", "daily"
    cvd_points: List[CVDDataPoint]

    class Config:
        from_attributes = True
