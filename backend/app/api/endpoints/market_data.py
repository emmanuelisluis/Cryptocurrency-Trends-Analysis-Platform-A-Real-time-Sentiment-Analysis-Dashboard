from fastapi import APIRouter, Depends, HTTPException, Path, Query # Added Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta # Added datetime, timedelta

from backend.app.services import order_book_service, trade_service
from backend.app.services.footprint_service import FootprintService # Added FootprintService
from backend.app.models.order_book_models import OrderBookSnapshotAPIResponse
from backend.app.models.trade_models import TradeAPIResponse, TradesAPIRequestParams
from backend.app.models.footprint_models import FootprintChartDataResponse # Added Footprint models
from backend.app.db.session import get_db

router = APIRouter()

@router.get(
    "/order_book/{exchange}/{symbol}",
    response_model=OrderBookSnapshotAPIResponse,
    summary="Get Latest Order Book Snapshot",
    description="Retrieves the most recent available order book snapshot for a given trading symbol on a specific exchange."
)
async def get_latest_order_book_api(
    exchange: str = Path(..., description="The name of the exchange (e.g., 'binance').", example="binance"),
    symbol: str = Path(..., description="The trading symbol (e.g., 'btcusdt').", example="btcusdt"),
    db: Session = Depends(get_db)
):
    """
    Endpoint to fetch the latest order book snapshot.
    - **exchange**: Name of the exchange.
    - **symbol**: Trading symbol.
    """
    order_book_data = order_book_service.get_latest_order_book(
        db=db,
        exchange_name=exchange,
        symbol_name=symbol
    )

    if not order_book_data:
        raise HTTPException(
            status_code=404,
            detail=f"Order book data not found for symbol '{symbol}' on exchange '{exchange}'."
        )

    return order_book_data


@router.get(
    "/trades/{exchange}/{symbol}",
    response_model=List[TradeAPIResponse],
    summary="Get Recent Trades",
    description="Retrieves a list of recent trades for a given trading symbol on a specific exchange, with optional filters."
)
async def get_recent_trades_api(
    exchange: str = Path(..., description="The name of the exchange (e.g., 'binance').", example="binance"),
    symbol: str = Path(..., description="The trading symbol (e.g., 'btcusdt').", example="btcusdt"),
    params: TradesAPIRequestParams = Depends(), # Inject and validate query parameters
    db: Session = Depends(get_db)
):
    """
    Endpoint to fetch recent trades.
    - **exchange**: Name of the exchange.
    - **symbol**: Trading symbol.
    - **Query Parameters (from TradesAPIRequestParams)**:
        - `limit`: Number of trades to return (default 100, max 1000).
        - `since_timestamp_utc`: ISO 8601 UTC timestamp to get trades after this time.
        - `min_volume`: Minimum trade volume.
    """
    trades_data = trade_service.get_recent_trades(
        db=db,
        exchange_name=exchange,
        symbol_name=symbol,
        params=params
    )

    # No 404 if list is empty, an empty list is a valid response for trades.
    return trades_data


@router.get(
    "/footprint/{exchange}/{symbol}",
    response_model=FootprintChartDataResponse,
    summary="Get Footprint Chart Data",
    description="Generates and retrieves data for a footprint chart, aggregating trades into time-based bars with volume at price levels."
)
async def get_footprint_chart_api( # Renamed from get_footprint_chart_data to avoid conflict if service method was named same
    exchange: str = Path(..., description="The name of the exchange (e.g., 'binance').", example="binance"),
    symbol: str = Path(..., description="The trading symbol (e.g., 'btcusdt').", example="btcusdt"),
    timeframe: str = Query(default="5m", description="Timeframe for bars (e.g., '1m', '5m', '1H', '1D').", examples=["1m", "15m", "1h", "4h", "1d"]),
    # Using string for start/end times, will convert to datetime. Pydantic might also do this with datetime type.
    start_time_utc: Optional[str] = Query(
        default=None,
        description="Start time in UTC (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS). Defaults to 24 hours ago.",
        examples=["2023-01-01T00:00:00Z"]
    ),
    end_time_utc: Optional[str] = Query(
        default=None,
        description="End time in UTC (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS). Defaults to now.",
        examples=["2023-01-01T12:00:00Z"]
    ),
    db: Session = Depends(get_db),
    footprint_service: FootprintService = Depends(FootprintService) # FastAPI will instantiate FootprintService
):
    """
    Endpoint to generate and fetch footprint chart data.
    - **exchange**: Name of the exchange.
    - **symbol**: Trading symbol.
    - **timeframe**: Aggregation period for each bar (e.g., "1m", "5m", "1H").
    - **start_time_utc**: Optional start time for fetching data. Defaults to 24 hours ago.
    - **end_time_utc**: Optional end time for fetching data. Defaults to current time.
    """

    # Parse and default date/time strings
    try:
        _end_dt = datetime.fromisoformat(end_time_utc.replace('Z', '+00:00')) if end_time_utc else datetime.utcnow()
        _start_dt = datetime.fromisoformat(start_time_utc.replace('Z', '+00:00')) if start_time_utc else _end_dt - timedelta(days=1)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {e}. Use ISO 8601 (YYYY-MM-DDTHH:MM:SSZ).")

    if _start_dt >= _end_dt:
        raise HTTPException(status_code=400, detail="Start time must be before end time.")

    # Limit query range for performance, e.g., max 30 days of 1m data, or fewer days for smaller timeframes.
    # This logic can be complex and depends on data density and performance characteristics.
    # Example: if timeframe_delta < timedelta(minutes=10) and (_end_dt - _start_dt) > timedelta(days=7):
    #    raise HTTPException(status_code=400, detail="For timeframes less than 10m, max query range is 7 days.")


    try:
        data = footprint_service.get_footprint_data(
            db=db,
            exchange=exchange,
            symbol=symbol,
            timeframe_str=timeframe,
            start_dt=_start_dt,
            end_dt=_end_dt
        )
        return data
    except ValueError as e: # Catch errors like unsupported timeframe from service or time_utils
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e: # Re-raise HTTPExceptions from service if any
        raise e
    except Exception as e:
        # Log the exception e with logger.error("...", exc_info=True) in real app
        raise HTTPException(status_code=500, detail=f"An internal error occurred while processing footprint data: {str(e)}")


# Ensure __init__.py for endpoints (already created)
# Ensure __init__.py for api (already created)
