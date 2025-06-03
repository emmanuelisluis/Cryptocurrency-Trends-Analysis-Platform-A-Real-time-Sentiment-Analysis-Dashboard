import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from backend.app.db.models import OrderBookSnapshotDB
from backend.app.models.order_book_models import OrderBookSnapshotAPIResponse, OrderBookLevelAPI, ImbalanceAtDepth, OBDGData # Added OBDGData
from backend.app.core.config import settings # For imbalance depth levels & OBDG levels (if moved to config)

logger = logging.getLogger(__name__)

# OBDG Calculation Parameters (can be moved to config.py if desired)
NEAR_MARKET_LEVELS_OBDG = 5
FAR_MARKET_START_LEVEL_OBDG = 6 # Start from the 6th level (index 5)
FAR_MARKET_END_LEVEL_OBDG = 20  # Up to the 20th level (index 19)

def _calculate_imbalances(
    bids: List[OrderBookLevelAPI],
    asks: List[OrderBookLevelAPI],
    depth_levels: List[int]
) -> List[ImbalanceAtDepth]:
    """
    Helper function to calculate order book imbalance at specified depth levels.
    Bids and asks are expected to be sorted with best prices first (bids: high to low, asks: low to high).
    """
    imbalances: List[ImbalanceAtDepth] = []

    # Ensure bids and asks are sorted correctly if not already guaranteed by caller
    # Bids: highest price first
    # Asks: lowest price first
    # The OrderBookSnapshotAPIResponse mapping already provides them in a list format,
    # but assumes the source (DB JSON) maintained the correct order from ingestion.
    # For calculation, we rely on this order.

    for N in depth_levels:
        top_n_bids = bids[:N]
        top_n_asks = asks[:N]

        bid_volume_at_depth = sum(level.quantity for level in top_n_bids)
        ask_volume_at_depth = sum(level.quantity for level in top_n_asks)

        total_volume = bid_volume_at_depth + ask_volume_at_depth

        imbalance_ratio = 0.5 # Default to perfect balance if no volume
        if total_volume > 0:
            imbalance_ratio = bid_volume_at_depth / total_volume

        imbalances.append(
            ImbalanceAtDepth(
                depth_level=N,
                bid_volume=bid_volume_at_depth,
                ask_volume=ask_volume_at_depth,
                imbalance_ratio=imbalance_ratio
            )
        )
    return imbalances

def _calculate_obdg(
    bids: List[OrderBookLevelAPI],
    asks: List[OrderBookLevelAPI],
    near_depth: int,
    far_start: int,
    far_end: int
) -> OBDGData:
    """
    Helper function to calculate Order Book Depth Gradient (OBDG) data.
    Assumes bids and asks are sorted best price first.
    """
    actual_num_bid_levels = len(bids)
    actual_num_ask_levels = len(asks)

    # Calculate near volumes
    near_bid_vol = sum(b.quantity for b in bids[:min(near_depth, actual_num_bid_levels)])
    near_ask_vol = sum(a.quantity for a in asks[:min(near_depth, actual_num_ask_levels)])

    # Calculate far volumes (adjust for 0-based indexing for slices)
    # Ensure far_start_idx is not less than near_depth to avoid overlap if misconfigured
    far_start_idx = max(near_depth, far_start -1)

    far_bid_vol = sum(b.quantity for b in bids[min(far_start_idx, actual_num_bid_levels):min(far_end, actual_num_bid_levels)])
    far_ask_vol = sum(a.quantity for a in asks[min(far_start_idx, actual_num_ask_levels):min(far_end, actual_num_ask_levels)])

    bid_ratio_nf = near_bid_vol / far_bid_vol if far_bid_vol > 0.0000001 else None # Avoid division by zero or tiny values
    ask_ratio_nf = near_ask_vol / far_ask_vol if far_ask_vol > 0.0000001 else None

    total_near_vol = near_bid_vol + near_ask_vol
    total_far_vol = far_bid_vol + far_ask_vol
    overall_gradient = total_near_vol / total_far_vol if total_far_vol > 0.0000001 else None

    return OBDGData(
        near_market_depth=near_depth,
        far_market_depth_start=far_start, # Report originally intended config
        far_market_depth_end=far_end,     # Report originally intended config
        bid_ratio_near_to_far=bid_ratio_nf,
        ask_ratio_near_to_far=ask_ratio_nf,
        overall_gradient_strength=overall_gradient
    )


def get_latest_order_book(db: Session, exchange_name: str, symbol_name: str) -> Optional[OrderBookSnapshotAPIResponse]:
    """
    Fetches the most recent order book snapshot for the given exchange and symbol.
    Calculates and includes order book imbalances and OBDG data.
    Uses synchronous SQLAlchemy session.
    """
    try:
        latest_order_book_db = (
            db.query(OrderBookSnapshotDB)
            .filter(
                OrderBookSnapshotDB.exchange == exchange_name.lower(),
                OrderBookSnapshotDB.symbol == symbol_name.lower()
            )
            .order_by(OrderBookSnapshotDB.timestamp.desc())
            .first()
        )

        if not latest_order_book_db:
            logger.info(f"No order book data found for {exchange_name}/{symbol_name}")
            return None

        bids_api: List[OrderBookLevelAPI] = []
        if latest_order_book_db.bids:
            for level in latest_order_book_db.bids:
                bids_api.append(OrderBookLevelAPI(price=level.get('price'), quantity=level.get('volume')))

        asks_api: List[OrderBookLevelAPI] = []
        if latest_order_book_db.asks:
            for level in latest_order_book_db.asks:
                asks_api.append(OrderBookLevelAPI(price=level.get('price'), quantity=level.get('volume')))

        # Calculate imbalances
        # Bids should be sorted best (highest price) first. Asks best (lowest price) first.
        # The data from DB is assumed to be in this order from ingestion.
        imbalance_data = _calculate_imbalances(
            bids=bids_api,
            asks=asks_api,
            depth_levels=settings.ORDER_BOOK_IMBALANCE_DEPTH_LEVELS
        )

        # Calculate OBDG data
        obdg_data = _calculate_obdg(
            bids=bids_api,
            asks=asks_api,
            near_depth=NEAR_MARKET_LEVELS_OBDG,
            far_start=FAR_MARKET_START_LEVEL_OBDG,
            far_end=FAR_MARKET_END_LEVEL_OBDG
        )

        response = OrderBookSnapshotAPIResponse(
            timestamp=latest_order_book_db.timestamp,
            symbol=latest_order_book_db.symbol,
            exchange=latest_order_book_db.exchange,
            bids=bids_api,
            asks=asks_api,
            last_update_id=latest_order_book_db.last_update_id,
            imbalances=imbalance_data,
            obdg_data=obdg_data # Populate the new field
        )
        return response

    except Exception as e:
        logger.error(f"Error fetching latest order book for {exchange_name}/{symbol_name}: {e}", exc_info=True)
        return None

# Ensure __init__.py exists in services directory (already created)
