"""
Pydantic models for Order Book related API responses.

These models define the structure for data related to order book snapshots,
including calculated metrics like imbalance at depth and order book depth gradient.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class OrderBookLevelAPI(BaseModel):
    """
    Represents a single price level in an order book for API responses.
    Uses 'quantity' for clarity over 'volume' in this context.
    """
    price: float = Field(..., description="Price for this order book level.")
    quantity: float = Field(..., description="Total quantity available at this price level.")

    class Config:
        from_attributes = True


class ImbalanceAtDepth(BaseModel):
    """
    Represents calculated order book imbalance at a specific depth.
    """
    depth_level: int = Field(..., description="Number of order book levels from BBO considered (e.g., 5, 10).")
    bid_volume: float = Field(..., description="Total volume of bids within this depth.")
    ask_volume: float = Field(..., description="Total volume of asks within this depth.")
    imbalance_ratio: float = Field(
        ...,
        description="Ratio of bid volume to total volume at this depth (bid_volume / (bid_volume + ask_volume)). Values > 0.5 indicate heavier bid side, < 0.5 indicate heavier ask side."
    )
    # Optional: Consider adding signed_imbalance_ratio if useful for frontend visualization.
    # signed_imbalance_ratio: Optional[float] = Field(None, description="Signed ratio: (bid_volume - ask_volume) / (bid_volume + ask_volume). Ranges -1 to 1.")

    class Config:
        from_attributes = True


class OBDGData(BaseModel): # Order Book Depth Gradient
    """
    Represents Order Book Depth Gradient (OBDG) metrics.
    Compares liquidity at "near market" depth vs "far market" depth.
    """
    near_market_depth: int = Field(..., description="Number of levels from BBO defined as 'near market'.")
    far_market_depth_start: int = Field(..., description="Starting level (from BBO) defined as 'far market'.")
    far_market_depth_end: int = Field(..., description="Ending level (from BBO) defined as 'far market'.")

    bid_ratio_near_to_far: Optional[float] = Field(None, description="Ratio of near bid volume to far bid volume (near_bid_vol / far_bid_vol). Null if far_bid_vol is zero.")
    ask_ratio_near_to_far: Optional[float] = Field(None, description="Ratio of near ask volume to far ask volume (near_ask_vol / far_ask_vol). Null if far_ask_vol is zero.")
    overall_gradient_strength: Optional[float] = Field(None, description="Ratio of total near volume to total far volume. Null if total_far_vol is zero.")

    class Config:
        from_attributes = True


class OrderBookSnapshotAPIResponse(BaseModel):
    """
    API response model for an order book snapshot, including bids, asks,
    imbalance data, and OBDG data.
    """
    timestamp: datetime = Field(..., description="Timestamp of the order book snapshot (UTC).")
    symbol: str = Field(..., description="Trading symbol (e.g., 'btcusdt').")
    exchange: str = Field(..., description="Exchange name (e.g., 'binance').")
    bids: List[OrderBookLevelAPI] = Field(..., description="List of bid levels, sorted highest price first.")
    asks: List[OrderBookLevelAPI] = Field(..., description="List of ask levels, sorted lowest price first.")
    last_update_id: Optional[int] = Field(None, description="For exchanges like Binance, the last update ID of the event(s) in this snapshot.")
    imbalances: Optional[List[ImbalanceAtDepth]] = Field(None, description="List of calculated order book imbalances at different depths.")
    obdg_data: Optional[OBDGData] = Field(None, description="Calculated Order Book Depth Gradient data.")

    class Config:
        from_attributes = True # Enables ORM mode for Pydantic V2
