import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from backend.app.db.models import OrderBookSnapshotDB
from backend.app.models.order_book_models import OrderBookSnapshotAPIResponse, OrderBookLevelAPI, ImbalanceAtDepth
from backend.app.core.config import settings # For imbalance depth levels

logger = logging.getLogger(__name__)

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

def get_latest_order_book(db: Session, exchange_name: str, symbol_name: str) -> Optional[OrderBookSnapshotAPIResponse]:
    """
    Fetches the most recent order book snapshot for the given exchange and symbol.
    Calculates and includes order book imbalances.
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

        response = OrderBookSnapshotAPIResponse(
            timestamp=latest_order_book_db.timestamp,
            symbol=latest_order_book_db.symbol,
            exchange=latest_order_book_db.exchange,
            bids=bids_api,
            asks=asks_api,
            last_update_id=latest_order_book_db.last_update_id,
            imbalances=imbalance_data # Populate the new field
        )
        return response

    except Exception as e:
        logger.error(f"Error fetching latest order book for {exchange_name}/{symbol_name}: {e}", exc_info=True)
        return None

# Ensure __init__.py exists in services directory (already created)
