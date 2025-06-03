from typing import List, Optional # datetime was already imported
from datetime import datetime
from pydantic import BaseModel, Field # Added Field

# This can be different from the one in exchange_data.py if API needs a different structure/naming
class OrderBookLevelAPI(BaseModel):
    price: float
    quantity: float # Using 'quantity' here for API clarity, instead of 'volume'

class ImbalanceAtDepth(BaseModel):
    depth_level: int # e.g., 5, 10, 20 levels from top
    bid_volume: float
    ask_volume: float
    # Imbalance ratio: (bid_volume / (bid_volume + ask_volume))
    # Value between 0 and 1. 0.5 means perfect balance. >0.5 means more bid volume. <0.5 means more ask volume.
    imbalance_ratio: float = Field(
        ...,
        description="Ratio of bid volume to total volume at this depth (bid_volume / (bid_volume + ask_volume)). Values > 0.5 indicate heavier bid side."
    )
    # Alternative: signed imbalance: (bid_volume - ask_volume) / (bid_volume + ask_volume)
    # signed_imbalance_ratio: Optional[float] = Field(
    #     None,
    #     description="Signed imbalance ratio ((bid_volume - ask_volume) / (bid_volume + ask_volume)). Values from -1 (all ask) to 1 (all bid)."
    # )

class OBDGData(BaseModel): # Order Book Depth Gradient
    near_market_depth: int # e.g., 5 levels (how many levels from BBO are considered "near")
    far_market_depth_start: int # e.g., 6 (start level for "far" depth)
    far_market_depth_end: int # e.g., 20 (end level for "far" depth)

    bid_ratio_near_to_far: Optional[float] = Field(None, description="Ratio of near bid volume to far bid volume (near_bid_vol / far_bid_vol)")
    ask_ratio_near_to_far: Optional[float] = Field(None, description="Ratio of near ask volume to far ask volume (near_ask_vol / far_ask_vol)")
    overall_gradient_strength: Optional[float] = Field(None, description="Ratio of total near volume to total far volume ((near_bid + near_ask) / (far_bid + far_ask))")

    class Config:
        from_attributes = True


class OrderBookSnapshotAPIResponse(BaseModel): # Modify existing one
    timestamp: datetime
    symbol: str
    exchange: str
    bids: List[OrderBookLevelAPI]
    asks: List[OrderBookLevelAPI]
    last_update_id: Optional[int] = None
    imbalances: Optional[List[ImbalanceAtDepth]] = None
    obdg_data: Optional[OBDGData] = None # Add this field

    class Config:
        # orm_mode = True # Pydantic V1
        from_attributes = True # Pydantic V2 for ORM mode
