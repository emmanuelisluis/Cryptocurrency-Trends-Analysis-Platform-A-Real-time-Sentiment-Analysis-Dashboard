"""
Service layer for handling order book related operations.

This module provides functions to retrieve and process order book snapshots
from the database. It includes calculations for derived metrics such as
order book imbalance at various depth levels and Order Book Depth Gradient (OBDG),
which can offer insights into market liquidity and potential price movements.
"""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # Specific exception for DB errors

from backend.app.core.config import settings # For accessing configuration like imbalance depths
from backend.app.db.models import OrderBookSnapshotDB # SQLAlchemy model for order book data
from backend.app.models.order_book_models import ( # Pydantic models for API responses and internal data structures
    ImbalanceAtDepth,
    OBDGData,
    OrderBookLevelAPI,
    OrderBookSnapshotAPIResponse,
)

logger = logging.getLogger(__name__)

# --- OBDG Calculation Parameters ---
# These parameters define the "near" and "far" regions of the order book for OBDG calculation.
# They could be moved to `settings.py` if they need to be more dynamically configurable
# (e.g., settings.ORDER_BOOK_OBDG_NEAR_DEPTH, settings.ORDER_BOOK_OBDG_FAR_START, etc.).
NEAR_MARKET_LEVELS_OBDG_DEFAULT: int = 5 # Number of levels from BBO considered "near market"
FAR_MARKET_START_LEVEL_OBDG_DEFAULT: int = 6 # Starting level (1-based index) for "far market" depth
FAR_MARKET_END_LEVEL_OBDG_DEFAULT: int = 20  # Ending level (1-based index) for "far market" depth

# Define a small epsilon value for float comparisons, particularly to avoid division by zero.
FLOAT_EPSILON: float = 1e-9


def _calculate_imbalances(
    bids: List[OrderBookLevelAPI],
    asks: List[OrderBookLevelAPI],
    depth_levels: List[int]
) -> List[ImbalanceAtDepth]:
    """
    Private helper function to calculate order book imbalance at specified depth levels.

    Imbalance is calculated as: BidVolume / (BidVolume + AskVolume) at a given depth.
    A value of 0.5 indicates perfect balance, > 0.5 indicates bid-side pressure,
    and < 0.5 indicates ask-side pressure.

    Args:
        bids (List[OrderBookLevelAPI]): A list of bid levels, where each level is an
            `OrderBookLevelAPI` object (price, quantity). Assumed to be sorted with the
            best bid (highest price) first.
        asks (List[OrderBookLevelAPI]): A list of ask levels, structured similarly to bids.
            Assumed to be sorted with the best ask (lowest price) first.
        depth_levels (List[int]): A list of integers representing the number of levels (N)
            from the best bid/ask to consider for each imbalance calculation
            (e.g., [1, 5, 10] for imbalance at top 1, 5, and 10 levels).

    Returns:
        List[ImbalanceAtDepth]: A list of `ImbalanceAtDepth` Pydantic models, each
            containing the calculated bid volume, ask volume, and imbalance ratio for a
            specified depth level.
    """
    imbalances: List[ImbalanceAtDepth] = []
    logger.debug(f"Calculating order book imbalances for depth levels: {depth_levels}")

    for n_levels in depth_levels:
        # Slice to get the top N levels for bids and asks.
        # If n_levels exceeds available depth, sum over available levels.
        current_bids = bids[:n_levels]
        current_asks = asks[:n_levels]

        # Sum the quantity (volume) at these N levels.
        bid_volume_at_depth = sum(level.quantity for level in current_bids if level.quantity is not None)
        ask_volume_at_depth = sum(level.quantity for level in current_asks if level.quantity is not None)
        total_volume_at_depth = bid_volume_at_depth + ask_volume_at_depth

        imbalance_ratio = 0.5 # Default to perfect balance if no volume or one side is zero.
        if total_volume_at_depth > FLOAT_EPSILON: # Avoid division by zero.
            imbalance_ratio = bid_volume_at_depth / total_volume_at_depth

        imbalances.append(
            ImbalanceAtDepth(
                depth_level=n_levels,
                bid_volume=bid_volume_at_depth,
                ask_volume=ask_volume_at_depth,
                imbalance_ratio=imbalance_ratio
            )
        )
        logger.debug(
            f"Imbalance at depth {n_levels}: BidVol={bid_volume_at_depth:.2f}, "
            f"AskVol={ask_volume_at_depth:.2f}, Ratio={imbalance_ratio:.3f}"
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
    Private helper function to calculate Order Book Depth Gradient (OBDG) data.

    OBDG measures the ratio of liquidity in "near market" levels to "far market" levels.
    It can indicate absorption or exhaustion of liquidity.
    - Bid Ratio > 1: More liquidity near the market on the bid side than further away.
    - Ask Ratio > 1: More liquidity near the market on the ask side than further away.
    - Overall Gradient: Ratio of total near liquidity to total far liquidity.

    Args:
        bids (List[OrderBookLevelAPI]): Sorted list of bid levels (best price first).
        asks (List[OrderBookLevelAPI]): Sorted list of ask levels (best price first).
        near_depth (int): Number of levels from the Best Bid/Offer (BBO) to be
            considered "near market".
        far_start (int): The starting level (1-based index) for the "far market" depth range.
            For example, if near_depth is 5, far_start might be 6.
        far_end (int): The ending level (1-based index) for the "far market" depth range.
            For example, up to the 20th level.

    Returns:
        OBDGData: A Pydantic model containing the calculated near/far ratios for bids and asks,
            and the overall gradient strength. Ratios can be None if far volume is zero.
    """
    logger.debug(f"Calculating OBDG: NearDepth={near_depth}, FarRange=({far_start}-{far_end})")

    actual_num_bid_levels = len(bids)
    actual_num_ask_levels = len(asks)

    # --- Calculate Near Market Volumes ---
    # Sum volume for the top `near_depth` levels, ensuring not to exceed available levels.
    near_bid_vol = sum(b.quantity for b in bids[:min(near_depth, actual_num_bid_levels)] if b.quantity is not None)
    near_ask_vol = sum(a.quantity for a in asks[:min(near_depth, actual_num_ask_levels)] if a.quantity is not None)

    # --- Calculate Far Market Volumes ---
    # Convert 1-based far_start/far_end to 0-based slice indices.
    # The far_start_idx should not overlap with near_depth.
    # The far_end_idx is exclusive for slicing.
    far_slice_start_idx = max(near_depth, far_start - 1) # Start after near_depth, adjust for 0-based.
    far_slice_end_idx = min(far_end, max(actual_num_bid_levels, actual_num_ask_levels)) # Don't exceed available levels.

    # Sum volume for the "far" levels, ensuring slices are valid and quantities are not None.
    far_bid_vol = sum(
        b.quantity for b in bids[min(far_slice_start_idx, actual_num_bid_levels) : min(far_slice_end_idx, actual_num_bid_levels)]
        if b.quantity is not None
    )
    far_ask_vol = sum(
        a.quantity for a in asks[min(far_slice_start_idx, actual_num_ask_levels) : min(far_slice_end_idx, actual_num_ask_levels)]
        if a.quantity is not None
    )

    # Calculate ratios, handling potential division by zero if far volume is negligible.
    bid_ratio_nf = near_bid_vol / far_bid_vol if far_bid_vol > FLOAT_EPSILON else None
    ask_ratio_nf = near_ask_vol / far_ask_vol if far_ask_vol > FLOAT_EPSILON else None

    total_near_vol = near_bid_vol + near_ask_vol
    total_far_vol = far_bid_vol + far_ask_vol
    overall_gradient = total_near_vol / total_far_vol if total_far_vol > FLOAT_EPSILON else None

    logger.debug(f"OBDG Results: NearBidVol={near_bid_vol:.2f}, FarBidVol={far_bid_vol:.2f}, BidRatio={bid_ratio_nf}")
    logger.debug(f"OBDG Results: NearAskVol={near_ask_vol:.2f}, FarAskVol={far_ask_vol:.2f}, AskRatio={ask_ratio_nf}")
    logger.debug(f"OBDG Results: TotalNearVol={total_near_vol:.2f}, TotalFarVol={total_far_vol:.2f}, OverallGradient={overall_gradient}")

    return OBDGData(
        near_market_depth=near_depth,
        far_market_depth_start=far_start,
        far_market_depth_end=far_end,
        bid_ratio_near_to_far=bid_ratio_nf,
        ask_ratio_near_to_far=ask_ratio_nf,
        overall_gradient_strength=overall_gradient
    )


def get_latest_order_book(
    db: Session,
    exchange_name: str,
    symbol_name: str
) -> Optional[OrderBookSnapshotAPIResponse]:
    """
    Fetches the most recent order book snapshot for a given exchange and symbol
    from the database. It then enriches this snapshot with calculated metrics:
    - Order book imbalances at various depth levels (configured in `settings`).
    - Order Book Depth Gradient (OBDG) data.

    Args:
        db (Session): The SQLAlchemy database session to use for querying.
        exchange_name (str): The name of the exchange (e.g., "binance").
            Will be lowercased for querying.
        symbol_name (str): The trading symbol (e.g., "btcusdt").
            Will be lowercased for querying.

    Returns:
        Optional[OrderBookSnapshotAPIResponse]: An `OrderBookSnapshotAPIResponse` Pydantic
            model containing the latest order book data along with calculated imbalances
            and OBDG metrics. Returns `None` if no order book data is found in the
            database for the specified exchange and symbol, or if an error occurs.
    """
    normalized_exchange = exchange_name.lower()
    normalized_symbol = symbol_name.lower()
    logger.info(f"Fetching latest order book for {normalized_exchange}/{normalized_symbol}")

    try:
        # Query the database for the most recent OrderBookSnapshotDB entry.
        latest_order_book_db_entry: Optional[OrderBookSnapshotDB] = (
            db.query(OrderBookSnapshotDB)
            .filter(
                OrderBookSnapshotDB.exchange == normalized_exchange,
                OrderBookSnapshotDB.symbol == normalized_symbol
            )
            .order_by(OrderBookSnapshotDB.timestamp.desc()) # Get the latest entry
            .first() # Expecting one or none
        )

        if not latest_order_book_db_entry:
            logger.warning(f"No order book data found in DB for {normalized_exchange}/{normalized_symbol}")
            return None

        # Map database JSONB lists (stored as list of dicts) to Pydantic OrderBookLevelAPI models.
        # Assumes that bids/asks from the DB are already sorted correctly (best price first).
        # Handles cases where price/volume might be missing in a level dict (though unlikely with proper data ingestion).
        bids_api: List[OrderBookLevelAPI] = [
            OrderBookLevelAPI(price=level.get('price'), quantity=level.get('volume'))
            for level in latest_order_book_db_entry.bids if isinstance(level, dict) and level.get('price') is not None and level.get('volume') is not None
        ]
        asks_api: List[OrderBookLevelAPI] = [
            OrderBookLevelAPI(price=level.get('price'), quantity=level.get('volume'))
            for level in latest_order_book_db_entry.asks if isinstance(level, dict) and level.get('price') is not None and level.get('volume') is not None
        ]

        # Calculate order book imbalances using depth levels from application settings.
        imbalance_data = _calculate_imbalances(
            bids=bids_api,
            asks=asks_api,
            depth_levels=settings.ORDER_BOOK_IMBALANCE_DEPTH_LEVELS
        )

        # Calculate OBDG data using default or configured parameters from settings.
        # getattr is used to safely access settings, falling back to defaults if not set.
        obdg_data = _calculate_obdg(
            bids=bids_api,
            asks=asks_api,
            near_depth=getattr(settings, 'ORDER_BOOK_OBDG_NEAR_DEPTH', NEAR_MARKET_LEVELS_OBDG_DEFAULT),
            far_start=getattr(settings, 'ORDER_BOOK_OBDG_FAR_START', FAR_MARKET_START_LEVEL_OBDG_DEFAULT),
            far_end=getattr(settings, 'ORDER_BOOK_OBDG_FAR_END', FAR_MARKET_END_LEVEL_OBDG_DEFAULT)
        )

        # Construct the API response model with the original snapshot data and calculated metrics.
        response = OrderBookSnapshotAPIResponse(
            timestamp=latest_order_book_db_entry.timestamp,
            symbol=latest_order_book_db_entry.symbol, # Already normalized
            exchange=latest_order_book_db_entry.exchange, # Already normalized
            bids=bids_api,
            asks=asks_api,
            last_update_id=latest_order_book_db_entry.last_update_id,
            imbalances=imbalance_data,
            obdg_data=obdg_data
        )
        logger.info(f"Successfully processed order book for {normalized_exchange}/{normalized_symbol} at {response.timestamp}")
        return response

    except SQLAlchemyError as e:
        logger.error(
            f"Database error fetching latest order book for {normalized_exchange}/{normalized_symbol}: {e}",
            exc_info=True # Include stack trace for DB errors
        )
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error fetching or processing latest order book for {normalized_exchange}/{normalized_symbol}: {e}",
            exc_info=True # Include stack trace for unexpected errors
        )
        return None

# Ensure __init__.py exists in the services directory (this was confirmed to be already created).
