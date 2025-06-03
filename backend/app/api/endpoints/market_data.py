from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta, date, time, timezone # Added date, time, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta, date, time, timezone

from backend.app.services import order_book_service, trade_service
from backend.app.services.footprint_service import FootprintService
from backend.app.services.volume_profile_service import VolumeProfileService
from backend.app.services.delta_analysis_service import DeltaAnalysisService
from backend.app.models.order_book_models import OrderBookSnapshotAPIResponse
from backend.app.models.trade_models import TradeAPIResponse, TradesAPIRequestParams
from backend.app.models.footprint_models import FootprintChartDataResponse
from backend.app.models.volume_profile_models import VolumeProfileData
from backend.app.models.delta_analysis_models import CVDChartDataResponse, AdvancedDeltaMetricsResponse # Added AdvancedDeltaMetricsResponse
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


@router.get(
    "/volume_profile/{exchange}/{symbol}",
    response_model=VolumeProfileData,
    summary="Get Volume Profile Data",
    description="Calculates and retrieves volume profile data (including POC and Value Area) for a given symbol, exchange, and time range or period type."
)
async def get_volume_profile_api( # Renamed to avoid conflict
    exchange: str = Path(..., description="The name of the exchange (e.g., 'binance').", example="binance"),
    symbol: str = Path(..., description="The trading symbol (e.g., 'btcusdt').", example="btcusdt"),
    profile_type: str = Query(
        default="daily",
        description="Type of profile: 'daily', 'weekly', 'monthly', 'range'.",
        examples=["daily", "weekly", "range"]
    ),
    date_utc: Optional[str] = Query( # Changed to string to allow date parsing with specific error handling
        default=None,
        description="Reference date in UTC (YYYY-MM-DD) for 'daily', 'weekly', 'monthly' profiles. Defaults to today UTC.",
        examples=["2023-10-27"]
    ),
    start_time_utc: Optional[str] = Query(
        default=None,
        description="Start datetime for 'range' profile (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ). Required if profile_type is 'range'.",
        examples=["2023-10-27T00:00:00Z"]
    ),
    end_time_utc: Optional[str] = Query(
        default=None,
        description="End datetime for 'range' profile (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ). Required if profile_type is 'range'.",
        examples=["2023-10-27T12:00:00Z"]
    ),
    tick_size: Optional[float] = Query(
        default=None,
        description="Symbol's price tick size for grouping price levels. If not provided, raw prices are used.",
        gt=0 # Tick size must be positive
    ),
    db: Session = Depends(get_db),
    volume_profile_service: VolumeProfileService = Depends(VolumeProfileService)
):
    _start_dt: datetime
    _end_dt: datetime

    try:
        if profile_type == "range":
            if not start_time_utc or not end_time_utc:
                raise HTTPException(status_code=400, detail="start_time_utc and end_time_utc are required for 'range' profile type.")
            _start_dt = datetime.fromisoformat(start_time_utc.replace('Z', '+00:00'))
            _end_dt = datetime.fromisoformat(end_time_utc.replace('Z', '+00:00'))
            if _start_dt.tzinfo is None: _start_dt = _start_dt.replace(tzinfo=timezone.utc) # Assume UTC if naive
            if _end_dt.tzinfo is None: _end_dt = _end_dt.replace(tzinfo=timezone.utc)

        else: # daily, weekly, monthly
            ref_date_obj = datetime.fromisoformat(date_utc).date() if date_utc else datetime.utcnow().date()

            if profile_type == "daily":
                _start_dt = datetime.combine(ref_date_obj, time.min, tzinfo=timezone.utc)
                _end_dt = datetime.combine(ref_date_obj, time.max, tzinfo=timezone.utc)
            elif profile_type == "weekly":
                start_of_week = ref_date_obj - timedelta(days=ref_date_obj.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                _start_dt = datetime.combine(start_of_week, time.min, tzinfo=timezone.utc)
                _end_dt = datetime.combine(end_of_week, time.max, tzinfo=timezone.utc)
            elif profile_type == "monthly":
                start_of_month = ref_date_obj.replace(day=1)
                # Robust way to get end of month: first day of next month minus one microsecond (or one day then time.max)
                next_month_start = (start_of_month.replace(day=28) + timedelta(days=4)).replace(day=1)
                end_of_month_day = next_month_start - timedelta(days=1)
                _start_dt = datetime.combine(start_of_month, time.min, tzinfo=timezone.utc)
                _end_dt = datetime.combine(end_of_month_day, time.max, tzinfo=timezone.utc)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported profile_type: {profile_type}. Choose from 'daily', 'weekly', 'monthly', 'range'.")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/datetime format: {e}. Use YYYY-MM-DD for date_utc or ISO 8601 for start/end times.")

    if _start_dt >= _end_dt:
        raise HTTPException(status_code=400, detail="Start time/date must be before end time/date.")

    try:
        data = volume_profile_service.get_volume_profile(
            db=db,
            exchange=exchange,
            symbol=symbol,
            start_dt=_start_dt,
            end_dt=_end_dt,
            profile_type=profile_type,
            price_tick_size=tick_size
        )
        return data
    except ValueError as e: # Catch specific errors from service if any (e.g. bad tick_size)
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e: # Catch DB errors from service
        # Log e with logger.error("...", exc_info=True)
        raise HTTPException(status_code=503, detail=str(e)) # Service unavailable due to DB issues
    except Exception as e:
        # Log e with logger.error("...", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")


@router.get(
    "/cvd/{exchange}/{symbol}",
    response_model=CVDChartDataResponse,
    summary="Get Cumulative Volume Delta (CVD) Data",
    description="Calculates and retrieves Cumulative Volume Delta based on underlying bar data."
)
async def get_cvd_api( # Renamed to avoid conflict
    exchange: str = Path(..., description="The name of the exchange.", example="binance"),
    symbol: str = Path(..., description="The trading symbol.", example="btcusdt"),
    timeframe: str = Query(default="5m", description="Timeframe of underlying bars (e.g., '1m', '5m', '1H').", examples=["1m", "5m", "1h"]),
    start_time_utc: Optional[str] = Query(
        default=None,
        description="Start time for data range in UTC (ISO 8601: YYYY-MM-DDTHH:MM:SSZ). Defaults to 24 hours ago."
    ),
    end_time_utc: Optional[str] = Query(
        default=None,
        description="End time for data range in UTC (ISO 8601: YYYY-MM-DDTHH:MM:SSZ). Defaults to now."
    ),
    reset_condition: str = Query(
        default="none",
        description="CVD reset condition: 'none' (continuous accumulation) or 'daily' (resets at start of each UTC day).",
        examples=["none", "daily"]
    ),
    db: Session = Depends(get_db),
    delta_service: DeltaAnalysisService = Depends(DeltaAnalysisService),
    footprint_service: FootprintService = Depends(FootprintService) # DeltaAnalysisService depends on FootprintService
):
    """
    Endpoint to fetch Cumulative Volume Delta (CVD) data.
    - **exchange**: Name of the exchange.
    - **symbol**: Trading symbol.
    - **timeframe**: Timeframe of the bars used to calculate delta (e.g., "1m", "5m").
    - **start_time_utc**: Optional start time. Defaults to 24 hours ago.
    - **end_time_utc**: Optional end time. Defaults to current time.
    - **reset_condition**: When to reset CVD accumulation ('none' or 'daily').
    """
    try:
        _end_dt = datetime.fromisoformat(end_time_utc.replace('Z', '+00:00')) if end_time_utc else datetime.now(timezone.utc)
        _start_dt = datetime.fromisoformat(start_time_utc.replace('Z', '+00:00')) if start_time_utc else _end_dt - timedelta(days=1)
        if _start_dt.tzinfo is None: _start_dt = _start_dt.replace(tzinfo=timezone.utc)
        if _end_dt.tzinfo is None: _end_dt = _end_dt.replace(tzinfo=timezone.utc)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {e}. Use ISO 8601 (YYYY-MM-DDTHH:MM:SSZ).")

    if _start_dt >= _end_dt:
        raise HTTPException(status_code=400, detail="Start time must be before end time.")

    if reset_condition not in ["none", "daily"]:
        raise HTTPException(status_code=400, detail="Invalid reset_condition. Allowed values are 'none' or 'daily'.")

    try:
        data = delta_service.get_cvd_data(
            db=db,
            footprint_service=footprint_service,
            exchange=exchange,
            symbol=symbol,
            timeframe_str=timeframe,
            start_dt=_start_dt,
            end_dt=_end_dt,
            reset_condition=reset_condition
        )
        return data
    except ValueError as e: # From timeframe parsing or other validation in services
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e: # E.g. DB error from underlying footprint service call
        # Log e with logger.error("...", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Service error: {str(e)}")
    except Exception as e:
        # Log e with logger.error("...", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")


@router.get(
    "/advanced_delta_metrics/{exchange}/{symbol}",
    response_model=AdvancedDeltaMetricsResponse,
    summary="Get Advanced Delta Metrics (DVPR, DMRV)",
    description="Calculates and retrieves Delta Volume Pressure Ratio (DVPR) and Delta Moving Average Rate of Change (DMRV)."
)
async def get_advanced_delta_metrics_api( # Renamed endpoint function
    exchange: str = Path(..., description="The name of the exchange.", example="binance"),
    symbol: str = Path(..., description="The trading symbol.", example="btcusdt"),
    timeframe: str = Query(default="5m", description="Timeframe of underlying bars (e.g., '1m', '5m', '1H').", examples=["1m", "5m", "1h"]),
    start_time_utc: Optional[str] = Query(
        default=None,
        description="Start time for data range in UTC (ISO 8601: YYYY-MM-DDTHH:MM:SSZ). Defaults to 24 hours ago."
    ),
    end_time_utc: Optional[str] = Query(
        default=None,
        description="End time for data range in UTC (ISO 8601: YYYY-MM-DDTHH:MM:SSZ). Defaults to now."
    ),
    atr_period: int = Query(default=14, ge=1, description="ATR calculation period."),
    dmrv_short_ma: int = Query(default=5, ge=1, description="Short MA period for DMRV delta."),
    dmrv_long_ma: int = Query(default=10, ge=1, description="Long MA period for DMRV delta."),
    db: Session = Depends(get_db),
    delta_service: DeltaAnalysisService = Depends(DeltaAnalysisService),
    footprint_service: FootprintService = Depends(FootprintService) # Required by DeltaAnalysisService
):
    """
    Endpoint to fetch Advanced Delta Metrics (DVPR, DMRV).
    - **exchange**: Name of the exchange.
    - **symbol**: Trading symbol.
    - **timeframe**: Timeframe of bars used for delta calculation.
    - **start_time_utc**: Optional start time. Defaults to 24 hours ago.
    - **end_time_utc**: Optional end time. Defaults to current time.
    - **atr_period**: Period for ATR calculation (used in DVPR).
    - **dmrv_short_ma**: Short MA period for DMRV.
    - **dmrv_long_ma**: Long MA period for DMRV.
    """
    try:
        # For datetime conversion, ensure timezone info is handled or assumed UTC
        _end_dt = datetime.fromisoformat(end_time_utc.replace('Z', '+00:00')) if end_time_utc else datetime.now(timezone.utc)
        _start_dt = datetime.fromisoformat(start_time_utc.replace('Z', '+00:00')) if start_time_utc else _end_dt - timedelta(days=1)
        if _start_dt.tzinfo is None: _start_dt = _start_dt.replace(tzinfo=timezone.utc)
        if _end_dt.tzinfo is None: _end_dt = _end_dt.replace(tzinfo=timezone.utc)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {e}. Use ISO 8601 (YYYY-MM-DDTHH:MM:SSZ).")

    if _start_dt >= _end_dt:
        raise HTTPException(status_code=400, detail="Start time must be before end time.")
    if dmrv_short_ma >= dmrv_long_ma:
        raise HTTPException(status_code=400, detail="DMRV short MA period must be less than long MA period.")

    try:
        data = delta_service.get_advanced_delta_metrics(
            db=db,
            footprint_service=footprint_service,
            exchange=exchange,
            symbol=symbol,
            timeframe_str=timeframe,
            start_dt=_start_dt,
            end_dt=_end_dt,
            atr_period=atr_period,
            dmrv_short_period=dmrv_short_ma,
            dmrv_long_period=dmrv_long_ma
        )
        return data
    except ValueError as e: # From timeframe parsing or other validation in services
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e: # E.g. DB error from underlying footprint service call
        # Log e with logger.error("...", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Service error: {str(e)}")
    except Exception as e:
        # Log e with logger.error("...", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")


# Ensure __init__.py for endpoints (already created)
# Ensure __init__.py for api (already created)
