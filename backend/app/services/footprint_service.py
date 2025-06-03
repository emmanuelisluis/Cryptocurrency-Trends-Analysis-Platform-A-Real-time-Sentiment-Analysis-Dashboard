import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
"""
Service layer for generating Footprint chart data.

This service fetches raw trade data, aggregates it into time-based bars,
and then for each bar, further aggregates volume by price level,
distinguishing between bid-aggressor and ask-aggressor volumes.
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd # Assumed to be installed
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException # For raising errors that can be handled by API layer

from backend.app.db.models import TradeDB
from backend.app.models.footprint_models import (
    FootprintBar,
    FootprintPriceLevel,
    FootprintChartDataResponse,
)
from backend.app.utils.time_utils import (
    map_timeframe_to_pandas_freq,
    parse_timeframe_to_timedelta,
)
# from backend.app.core.config import settings # Uncomment if specific settings are needed

logger = logging.getLogger(__name__)


class FootprintService:
    """
    Service class for generating footprint chart data.
    """

    def get_footprint_data(
        self,
        db: Session,
        exchange: str,
        symbol: str,
        timeframe_str: str,
        start_dt: datetime,
        end_dt: datetime
    ) -> FootprintChartDataResponse:
        """
        Generates footprint chart data for a given market, timeframe, and date range.

        Args:
            db: SQLAlchemy database session.
            exchange: Exchange name (e.g., "binance").
            symbol: Trading symbol (e.g., "btcusdt").
            timeframe_str: Timeframe string (e.g., "1m", "5m", "1H").
            start_dt: Start datetime (UTC) for data fetching.
            end_dt: End datetime (UTC) for data fetching.

        Returns:
            FootprintChartDataResponse containing the generated footprint bars.

        Raises:
            ValueError: If the timeframe string is invalid.
            HTTPException: If there's a database error during trade fetching.
        """

        logger.info(
            f"Generating footprint data for {exchange.lower()}/{symbol.lower()} | "
            f"Timeframe: {timeframe_str} | Range: {start_dt} to {end_dt}"
        )

        # Validate and parse timeframe string (raises ValueError if invalid)
        timeframe_delta = parse_timeframe_to_timedelta(timeframe_str)
        pandas_timeframe = map_timeframe_to_pandas_freq(timeframe_str)
        logger.debug(f"Parsed timeframe: delta={timeframe_delta}, pandas_freq='{pandas_timeframe}'")

        # 1. Fetch trades from DB
        # Ensure aggressor_side is not None as it's crucial for footprint calculation.
        query = (
            db.query(TradeDB.timestamp, TradeDB.price, TradeDB.volume, TradeDB.aggressor_side)
            .filter(
                TradeDB.exchange == exchange.lower(),
                TradeDB.symbol == symbol.lower(),
                TradeDB.timestamp >= start_dt,
                TradeDB.timestamp < end_dt, # Standard practice: end_dt is exclusive
                TradeDB.aggressor_side.isnot(None)
            )
            .order_by(TradeDB.timestamp.asc()) # Order by time for correct resampling
        )

        try:
            trades_df = pd.read_sql(query.statement, db.bind)
            logger.debug(f"Fetched {len(trades_df)} trades from database.")
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching trades for footprint: {e}", exc_info=True)
            # Propagate as an HTTPException to be handled by the API layer
            raise HTTPException(status_code=503, detail=f"Database error while fetching trades: {e}")
        except Exception as e: # Catch other pandas/DB read errors
            logger.error(f"Unexpected error reading trades into DataFrame: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Unexpected error reading trades: {e}")


        if trades_df.empty:
            logger.info("No trades found for the given criteria to generate footprints.")
            return FootprintChartDataResponse(exchange=exchange, symbol=symbol, timeframe=timeframe_str, bars=[])

        # Ensure timestamp is pandas datetime and set as index (should be UTC from DB)
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], utc=True)
        trades_df.set_index('timestamp', inplace=True)

        # 2. Resample trades into bars to get OHLC data per interval
        # The 'rule' for resample should be a Pandas frequency string (e.g., '1T', '5T', '1H').
        logger.info(f"Resampling trades to '{pandas_timeframe}' timeframe for OHLC...")
        ohlc_df = trades_df['price'].resample(rule=pandas_timeframe).ohlc()
        # Drop rows where all OHLC values are NaN (bars with no trades)
        ohlc_df.dropna(how='all', inplace=True)

        if ohlc_df.empty:
            logger.info("OHLC data is empty after resampling (no trades in any interval).")
            return FootprintChartDataResponse(exchange=exchange, symbol=symbol, timeframe=timeframe_str, bars=[])

        footprint_bars: List[FootprintBar] = []
        logger.info(f"Aggregating trades into {len(ohlc_df)} footprint bars...")

        # 3. For each OHLC bar, aggregate bid/ask volumes at each price level
        for bar_start_timestamp_pd, ohlc_data in ohlc_df.iterrows():
            # bar_start_timestamp_pd is a pandas Timestamp object
            bar_start_time_dt = bar_start_timestamp_pd.to_pydatetime() # Convert to Python datetime
            bar_end_time_dt = bar_start_time_dt + timeframe_delta

            # Filter original trades that fall within this specific bar's time range
            bar_trades_df = trades_df[
                (trades_df.index >= bar_start_time_dt) &
                (trades_df.index < bar_end_time_dt)
            ]

            if bar_trades_df.empty: # Should generally not happen if ohlc_df had an entry for this timestamp
                logger.debug(f"No trades found for bar starting at {bar_start_time_dt} (unexpected).")
                continue

            # Aggregate volume by price and aggressor side for this bar
            price_level_aggregation: Dict[float, Dict[str, float]] = defaultdict(lambda: {'bid_volume': 0.0, 'ask_volume': 0.0})

            for _, trade_row in bar_trades_df.iterrows():
                price = trade_row['price']
                volume = trade_row['volume']
                aggressor = trade_row['aggressor_side'] # Assumed to be 'buy' or 'sell'

                if aggressor == 'buy': # Buyer was aggressor (hit the ask)
                    price_level_aggregation[price]['ask_volume'] += volume
                elif aggressor == 'sell': # Seller was aggressor (hit the bid)
                    price_level_aggregation[price]['bid_volume'] += volume

            bar_price_levels: List[FootprintPriceLevel] = []
            bar_total_volume_calculated = 0.0 # Sum of volumes from price levels
            bar_total_delta_calculated = 0.0  # Sum of deltas from price levels

            # Sort price levels for consistent output in the FootprintBar
            sorted_prices = sorted(price_level_aggregation.keys())

            for price in sorted_prices:
                agg_data = price_level_aggregation[price]
                bid_vol = agg_data['bid_volume']
                ask_vol = agg_data['ask_volume']
                delta_at_price = ask_vol - bid_vol
                total_vol_at_price = bid_vol + ask_vol

                bar_price_levels.append(FootprintPriceLevel(
                    price=price,
                    bid_volume=bid_vol,
                    ask_volume=ask_vol,
                    delta=delta_at_price,
                    total_volume=total_vol_at_price
                ))
                bar_total_volume_calculated += total_vol_at_price
                bar_total_delta_calculated += delta_at_price

            footprint_bars.append(FootprintBar(
                timestamp=bar_start_time_dt,
                open=float(ohlc_data['open']), # Ensure float type
                high=float(ohlc_data['high']),
                low=float(ohlc_data['low']),
                close=float(ohlc_data['close']),
                total_volume=bar_total_volume_calculated, # Use sum from levels for consistency
                total_delta=bar_total_delta_calculated,   # Use sum from levels
                price_levels=bar_price_levels
            ))

        logger.info(f"Successfully generated {len(footprint_bars)} footprint bars.")
        return FootprintChartDataResponse(
            exchange=exchange.lower(), # Standardize output
            symbol=symbol.lower(),
            timeframe=timeframe_str,
            bars=footprint_bars
        )
