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


class OrderBookSnapshotAPIResponse(BaseModel):
    timestamp: datetime
    symbol: str
    exchange: str
    bids: List[OrderBookLevelAPI]
    asks: List[OrderBookLevelAPI]
    last_update_id: Optional[int] = None
    imbalances: Optional[List[ImbalanceAtDepth]] = None # Added this field

    class Config:
        # orm_mode = True # Pydantic V1
        from_attributes = True # Pydantic V2 for ORM mode
