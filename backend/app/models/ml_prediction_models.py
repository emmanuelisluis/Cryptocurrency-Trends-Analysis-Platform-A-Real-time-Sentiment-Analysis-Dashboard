"""
Pydantic models for ML prediction API requests and responses.

These models define the expected input features and output structures
for various machine learning predictions offered by the application.
"""
from datetime import datetime
from typing import List, Optional, Dict # Dict used for schema_extra examples

from pydantic import BaseModel, Field, ConfigDict # Added ConfigDict for Pydantic V2 model_config


# --- Momentum Sustainability Score ---
class MomentumSustainabilityInputFeatures(BaseModel):
    """
    Input features for predicting the sustainability of observed market momentum.
    """
    bar_timestamp: datetime = Field(..., description="Timestamp of the bar/event being analyzed (UTC).")
    bar_delta: float = Field(..., description="Delta of the bar (Ask Volume - Bid Volume).")
    bar_volume: float = Field(..., description="Total volume of the bar.")

    recent_cvd_slope: Optional[float] = Field(None, description="Slope of Cumulative Volume Delta over a recent period (e.g., last N bars).")
    market_volatility_atr: Optional[float] = Field(None, description="Current Average True Range (ATR) as a measure of market volatility.")
    # other_contextual_features: Optional[Dict[str, float]] = Field(None, description="Other relevant contextual features.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "bar_timestamp": "2023-10-27T10:00:00Z",
                "bar_delta": 150.5,
                "bar_volume": 1200.75,
                "recent_cvd_slope": 0.5,
                "market_volatility_atr": 0.05
            }
        }
    )


class MomentumSustainabilityOutput(BaseModel):
    """
    Output structure for the momentum sustainability prediction.
    """
    timestamp_event: datetime = Field(..., description="Timestamp of the event for which prediction is made (UTC).")
    sustainability_score: float = Field(..., ge=0.0, le=10.0, description="Predicted sustainability score (0-10). Higher means more likely to sustain.")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Model's confidence in the prediction (0-1).")
    model_version: Optional[str] = Field(None, description="Version of the model used for this prediction.")
    # explanation: Optional[Dict[str, float]] = Field(None, description="Contributing factors or feature importance, if available.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "timestamp_event": "2023-10-27T10:00:00Z",
                "sustainability_score": 7.5,
                "confidence": 0.85,
                "model_version": "ms_v0.1.2"
            }
        }
    )


# --- Breakout Viability Prediction ---
class BreakoutViabilityInputFeatures(BaseModel):
    """
    Input features for predicting the viability of a price breakout.
    """
    breakout_price_level: float = Field(..., description="The price level being tested for breakout.")
    bar_timestamp_breakout_attempt: datetime = Field(..., description="Timestamp of the bar attempting the breakout (UTC).")
    volume_at_breakout_bar: float = Field(..., description="Volume of the bar attempting the breakout.")
    delta_at_breakout_bar: float = Field(..., description="Delta of the bar attempting the breakout.")

    recent_volatility_atr: Optional[float] = Field(None, description="ATR as a measure of recent volatility.")
    distance_from_key_level: Optional[float] = Field(None, description="Distance from a known key S/R level. Positive if price is above, negative if below.")
    # order_book_pressure_at_level: Optional[float] = Field(None, description="Order book imbalance or volume at/near the breakout level before the attempt.")
    # speed_of_price_movement_to_level: Optional[float] = Field(None, description="How quickly price approached the breakout level.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "breakout_price_level": 50000.0,
                "bar_timestamp_breakout_attempt": "2023-10-27T10:30:00Z",
                "volume_at_breakout_bar": 50.0,
                "delta_at_breakout_bar": 25.0,
                "recent_volatility_atr": 150.0
            }
        }
    )


class BreakoutViabilityOutput(BaseModel):
    """
    Output structure for the breakout viability prediction.
    """
    timestamp_event: datetime = Field(..., description="Timestamp of the breakout attempt event (UTC).")
    breakout_price_level: float = Field(..., description="The price level that was tested.")
    probability_true_breakout: float = Field(..., ge=0.0, le=1.0, description="Probability that this is a true breakout (will sustain).")
    probability_false_breakout: float = Field(..., ge=0.0, le=1.0, description="Probability that this is a false breakout (will fail/reverse).")
    model_version: Optional[str] = Field(None, description="Version of the model used for this prediction.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "timestamp_event": "2023-10-27T10:30:00Z",
                "breakout_price_level": 50000.0,
                "probability_true_breakout": 0.72,
                "probability_false_breakout": 0.28,
                "model_version": "bv_v0.1.0"
            }
        }
    )


# --- Absorption Event Outcome Classification ---
class AbsorptionEventInputFeatures(BaseModel):
    """
    Input features for classifying the outcome of an absorption event.
    """
    event_timestamp: datetime = Field(..., description="Timestamp of the bar/event identified as absorption (UTC).")
    absorption_price_level: float = Field(..., description="Price level where absorption is identified.")
    volume_at_absorption_level: float = Field(..., description="Sum of bid_volume + ask_volume at this price level in the bar.")
    delta_at_absorption_level: float = Field(..., description="Ask volume - Bid volume at this price level in the bar.")
    total_bar_volume: float = Field(..., description="Total volume of the bar where absorption occurred.")
    total_bar_delta: float = Field(..., description="Total delta of the bar where absorption occurred.")

    price_action_leading_up: Optional[str] = Field(None, description="Categorical: e.g., 'approaching_from_below', 'approaching_from_above', 'ranging'.")
    order_book_pressure_bids: Optional[float] = Field(None, description="Sum of volume on N bid levels below absorption level just before event.")
    order_book_pressure_asks: Optional[float] = Field(None, description="Sum of volume on N ask levels above absorption level just before event.")
    # market_volatility_atr: Optional[float] = Field(None, description="ATR as a measure of volatility around the event.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "event_timestamp": "2023-10-27T11:00:00Z",
                "absorption_price_level": 49500.0,
                "volume_at_absorption_level": 75.0,
                "delta_at_absorption_level": -20.0,
                "total_bar_volume": 200.0,
                "total_bar_delta": -5.0,
                "price_action_leading_up": "approaching_from_above"
            }
        }
    )


class AbsorptionOutcomeOutput(BaseModel):
    """
    Output structure for the absorption event outcome prediction.
    """
    timestamp_event: datetime = Field(..., description="Timestamp of the absorption event (UTC).")
    absorption_price_level: float = Field(..., description="Price level of the identified absorption.")
    predicted_outcome_label: str = Field(..., description="Predicted outcome: 'Reversal', 'Continuation', 'Consolidation'.")
    probability_reversal: float = Field(..., ge=0.0, le=1.0, description="Probability of a Reversal outcome.")
    probability_continuation: float = Field(..., ge=0.0, le=1.0, description="Probability of a Continuation outcome.")
    probability_consolidation: float = Field(..., ge=0.0, le=1.0, description="Probability of a Consolidation outcome.")
    model_version: Optional[str] = Field(None, description="Version of the model used for this prediction.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "timestamp_event": "2023-10-27T11:00:00Z",
                "absorption_price_level": 49500.0,
                "predicted_outcome_label": "Reversal",
                "probability_reversal": 0.65,
                "probability_continuation": 0.25,
                "probability_consolidation": 0.10,
                "model_version": "ao_v0.1.1"
            }
        }
    )
