"""
Pydantic models for Delta Analysis related API responses.

This includes models for Cumulative Volume Delta (CVD),
Average True Range (ATR - primarily for internal use/calculations),
Delta Volume Pressure Ratio (DVPR), and Delta Moving Average Rate of Change (DMRV).
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CVDDataPoint(BaseModel):
    """
    Represents a single data point in a Cumulative Volume Delta series.
    """
    timestamp: datetime = Field(..., description="Timestamp for this CVD value (typically end of bar).")
    cvd_value: float = Field(..., description="Cumulative Volume Delta value.")

    class Config:
        from_attributes = True


class CVDChartDataResponse(BaseModel):
    """
    API response model for Cumulative Volume Delta (CVD) chart data.
    """
    exchange: str = Field(..., description="Exchange name.")
    symbol: str = Field(..., description="Trading symbol.")
    timeframe: str = Field(..., description="Timeframe of the underlying bars used for delta calculation (e.g., '1m', '5m').")
    reset_condition: str = Field(..., description="Condition under which CVD was reset (e.g., 'none', 'daily').")
    cvd_points: List[CVDDataPoint] = Field(..., description="List of CVD data points.")

    class Config:
        from_attributes = True


# --- Models for Advanced Delta Metrics ---

class ATRDataPoint(BaseModel):
    """
    Represents a single Average True Range (ATR) data point.
    Mainly for internal calculations but defined for clarity.
    """
    timestamp: datetime = Field(..., description="Timestamp for this ATR value.")
    atr_value: float = Field(..., description="Calculated ATR value.")

    class Config:
        from_attributes = True


class DVPRDataPoint(BaseModel):
    """
    Represents a single data point for Delta Volume Pressure Ratio (DVPR).
    DVPR = Bar Delta / (Bar Volume * Bar ATR)
    """
    timestamp: datetime = Field(..., description="Timestamp of the bar.")
    dvpr_value: Optional[float] = Field(None, description="Calculated DVPR value. Can be null if ATR or Volume is zero/unavailable.")
    bar_delta: float = Field(..., description="Delta of the bar (Ask Volume - Bid Volume).")
    bar_volume: float = Field(..., description="Total volume of the bar.")
    bar_atr: Optional[float] = Field(None, description="Average True Range (ATR) for the bar's period. Can be null if not calculable.")

    class Config:
        from_attributes = True


class DMRVDataPoint(BaseModel):
    """
    Represents a single data point for Delta Moving Average Rate of Change/Value (DMRV).
    DMRV = Short-term MA of Delta - Long-term MA of Delta.
    """
    timestamp: datetime = Field(..., description="Timestamp of the bar.")
    short_delta_ma: Optional[float] = Field(None, description="Short-term moving average of bar deltas.")
    long_delta_ma: Optional[float] = Field(None, description="Long-term moving average of bar deltas.")
    dmrv_value: Optional[float] = Field(None, description="Calculated DMRV value (Short MA - Long MA).")
    # Optional: Add dmrv_value_diff for rate of change if needed later.
    # dmrv_value_diff: Optional[float] = Field(None, description="Change from the previous DMRV value.")

    class Config:
        from_attributes = True


class AdvancedDeltaMetricsResponse(BaseModel):
    """
    API response model for advanced delta metrics, including DVPR and DMRV.
    """
    exchange: str = Field(..., description="Exchange name.")
    symbol: str = Field(..., description="Trading symbol.")
    timeframe: str = Field(..., description="Timeframe of the bars used for calculations.")
    dvpr_points: List[DVPRDataPoint] = Field(..., description="List of DVPR data points.")
    dmrv_points: List[DMRVDataPoint] = Field(..., description="List of DMRV data points.")

    class Config:
        from_attributes = True
