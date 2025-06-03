"""
Service layer for handling trade data operations.

This module provides functions to retrieve recent trade data from the database,
allowing for filtering based on criteria such as time range and minimum volume.
It interfaces between the database models and the API response models.
"""
import logging
from datetime import datetime # For type hinting, especially with params.since_timestamp_utc
from typing import List, Optional # Optional is not strictly needed here anymore but good practice.

from sqlalchemy import desc # For ordering results in descending order of timestamp
from sqlalchemy.orm import Session # For type hinting the database session
from sqlalchemy.exc import SQLAlchemyError # To catch database-specific exceptions

from backend.app.db.models import TradeDB # The SQLAlchemy model for trades
from backend.app.models.trade_models import TradeAPIResponse, TradesAPIRequestParams # Pydantic models

logger = logging.getLogger(__name__)

def get_recent_trades(
    db: Session,
    exchange_name: str,
    symbol_name: str,
    params: TradesAPIRequestParams
) -> List[TradeAPIResponse]:
    """
    Fetches recent trades for a given exchange and symbol from the database,
    applying optional filtering based on provided parameters.

    The function queries the `TradeDB` table, normalizes exchange and symbol names
    to lowercase for consistent querying, and applies filters for:
    - `since_timestamp_utc`: Trades occurring after this timestamp.
    - `min_volume`: Trades with volume greater than or equal to this value.
    Results are ordered by timestamp in descending order (most recent first)
    and limited by `params.limit`.

    Args:
        db (Session): The SQLAlchemy database session to use for the query.
        exchange_name (str): The name of the exchange (e.g., "binance").
            This will be converted to lowercase.
        symbol_name (str): The trading symbol (e.g., "btcusdt").
            This will be converted to lowercase.
        params (TradesAPIRequestParams): A Pydantic model containing filter parameters:
            - `limit` (int): Maximum number of trades to return.
            - `since_timestamp_utc` (Optional[datetime]): If provided, only trades
              after this UTC timestamp are returned. Pydantic V2 / FastAPI typically
              handle string-to-datetime conversion for query parameters.
            - `min_volume` (Optional[float]): If provided, only trades with volume
              greater than or equal to this value are returned.

    Returns:
        List[TradeAPIResponse]: A list of `TradeAPIResponse` Pydantic models,
            representing the fetched trades. Returns an empty list if no trades
            match the criteria or if a database/unexpected error occurs.
    """
    normalized_exchange = exchange_name.lower()
    normalized_symbol = symbol_name.lower()

    try:
        logger.debug(
            f"Fetching trades for {normalized_exchange}/{normalized_symbol} with params: "
            f"Limit={params.limit}, Since={params.since_timestamp_utc}, MinVol={params.min_volume}"
        )

        # Start building the query against the TradeDB table
        query = (
            db.query(TradeDB)
            .filter(
                TradeDB.exchange == normalized_exchange,
                TradeDB.symbol == normalized_symbol
            )
        )

        # Apply optional filter: trades since a specific timestamp
        if params.since_timestamp_utc:
            # Pydantic V2 with FastAPI should automatically parse ISO string to datetime.
            # Ensure this datetime is timezone-aware (UTC ideally) or handled consistently.
            # If `params.since_timestamp_utc` is naive, comparison with aware `TradeDB.timestamp` might behave unexpectedly
            # depending on DB and SQLAlchemy setup. Assuming `TradeDB.timestamp` is UTC.
            query = query.filter(TradeDB.timestamp > params.since_timestamp_utc)

        # Apply optional filter: minimum trade volume
        if params.min_volume is not None and params.min_volume > 0: # `ge=0` in Pydantic, but explicit check for >0 is fine
            query = query.filter(TradeDB.volume >= params.min_volume)

        # Apply ordering (most recent first) and limit the number of results
        query = query.order_by(desc(TradeDB.timestamp)).limit(params.limit)

        # Execute the query
        recent_trades_db: List[TradeDB] = query.all()

        logger.info(f"Retrieved {len(recent_trades_db)} trades from DB for {normalized_exchange}/{normalized_symbol}.")

        # Map SQLAlchemy model instances to Pydantic API response models.
        # `TradeAPIResponse.from_orm(trade_db)` handles the conversion.
        trades_api: List[TradeAPIResponse] = [
            TradeAPIResponse.from_orm(trade_db) for trade_db in recent_trades_db
        ]

        return trades_api

    except SQLAlchemyError as e:
        logger.error(
            f"Database error fetching recent trades for {normalized_exchange}/{normalized_symbol}: {e}",
            exc_info=True # Include stack trace for DB errors
        )
        # In case of a database error, return an empty list.
        # Depending on application requirements, a custom service exception could be raised here
        # to be handled by an exception handler in the API layer for a more specific HTTP error response.
        return []
    except Exception as e:
        logger.error(
            f"Unexpected error fetching recent trades for {normalized_exchange}/{normalized_symbol}: {e}",
            exc_info=True # Include stack trace for any other unexpected errors
        )
        # Return an empty list for other unexpected errors as well.
        return []
