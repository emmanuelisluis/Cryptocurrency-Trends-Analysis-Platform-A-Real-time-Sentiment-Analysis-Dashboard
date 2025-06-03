import logging
from typing import List, Optional
from datetime import datetime # For type hinting if converting string timestamp
from sqlalchemy.orm import Session
from sqlalchemy import desc # For ordering

from backend.app.db.models import TradeDB
from backend.app.models.trade_models import TradeAPIResponse, TradesAPIRequestParams

logger = logging.getLogger(__name__)

def get_recent_trades(
    db: Session,
    exchange_name: str,
    symbol_name: str,
    params: TradesAPIRequestParams
) -> List[TradeAPIResponse]:
    """
    Fetches recent trades for a given exchange and symbol, with optional filtering.
    Uses synchronous SQLAlchemy session.
    """
    try:
        query = (
            db.query(TradeDB)
            .filter(
                TradeDB.exchange == exchange_name.lower(),
                TradeDB.symbol == symbol_name.lower()
            )
        )

        # Apply optional filters
        if params.since_timestamp_utc:
            try:
                # Attempt to parse the ISO 8601 string to datetime
                # Pydantic v2 might do this automatically if the model field is datetime,
                # but if it's string in Pydantic model, manual parse needed here.
                # For simplicity, assuming params.since_timestamp_utc is already a datetime if Pydantic model has it as datetime,
                # or it's a string that needs parsing if Pydantic model has it as string.
                # The current Pydantic model has it as Optional[str].
                parsed_since_timestamp = datetime.fromisoformat(params.since_timestamp_utc.replace('Z', '+00:00'))
                query = query.filter(TradeDB.timestamp > parsed_since_timestamp)
            except ValueError:
                logger.warning(f"Invalid since_timestamp_utc format: {params.since_timestamp_utc}. Ignoring filter.")
                # Or raise HTTPException(400, "Invalid timestamp format") from endpoint

        if params.min_volume is not None and params.min_volume > 0:
            query = query.filter(TradeDB.volume >= params.min_volume)

        # Apply ordering and limit
        query = query.order_by(desc(TradeDB.timestamp)).limit(params.limit)

        recent_trades_db = query.all()

        # Map SQLAlchemy model instances to Pydantic API response models
        trades_api: List[TradeAPIResponse] = []
        for trade_db in recent_trades_db:
            trades_api.append(TradeAPIResponse.from_orm(trade_db))

        return trades_api

    except Exception as e:
        logger.error(f"Error fetching recent trades for {exchange_name}/{symbol_name}: {e}", exc_info=True)
        # In a real app, you might want to distinguish between DB errors and other errors
        return [] # Return empty list on error, or re-raise

# Ensure __init__.py exists in services directory (already created)
