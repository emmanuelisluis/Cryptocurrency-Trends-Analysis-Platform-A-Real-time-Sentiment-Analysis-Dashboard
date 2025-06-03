import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict
import pandas as pd # This import will fail if pandas is not installed

from backend.app.db.models import TradeDB
from backend.app.models.footprint_models import FootprintBar, FootprintPriceLevel, FootprintChartDataResponse
from backend.app.utils.time_utils import parse_timeframe_to_timedelta, map_timeframe_to_pandas_freq
# from backend.app.core.config import settings # Uncomment if settings are needed

logger = logging.getLogger(__name__)

class FootprintService:
    def get_footprint_data(
        self,
        db: Session,
        exchange: str,
        symbol: str,
        timeframe_str: str,
        start_dt: datetime,
        end_dt: datetime
    ) -> FootprintChartDataResponse:

        # Validate and parse timeframe string
        try:
            timeframe_delta = parse_timeframe_to_timedelta(timeframe_str)
            pandas_timeframe = map_timeframe_to_pandas_freq(timeframe_str)
        except ValueError as e:
            logger.error(f"Invalid timeframe processing: {e}")
            raise # Re-raise to be caught by endpoint and returned as HTTP 400

        # 1. Fetch trades from DB
        logger.info(f"Fetching trades for {exchange}/{symbol} from {start_dt} to {end_dt}")
        query = (
            db.query(TradeDB.timestamp, TradeDB.price, TradeDB.volume, TradeDB.aggressor_side)
            .filter(
                TradeDB.exchange == exchange.lower(),
                TradeDB.symbol == symbol.lower(),
                TradeDB.timestamp >= start_dt,
                TradeDB.timestamp < end_dt, # Use < end_dt for consistency with pandas resampling
                TradeDB.aggressor_side.isnot(None) # Crucial for footprint
            )
            .order_by(TradeDB.timestamp.asc())
        )

        try:
            trades_df = pd.read_sql(query.statement, db.bind)
        except Exception as e: # Catch pandas/DB read errors
            logger.error(f"Error reading trades into DataFrame: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Database error while fetching trades.") # Example, specific error handling might be better

        if trades_df.empty:
            logger.info("No trades found for the given criteria.")
            return FootprintChartDataResponse(exchange=exchange, symbol=symbol, timeframe=timeframe_str, bars=[])

        # Ensure timestamp is datetime and set as index
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], utc=True) # Ensure UTC
        trades_df.set_index('timestamp', inplace=True)

        # 2. Resample trades into bars (OHLC) based on price
        #    'rule' argument for resample should be like '1T' (1 min), '1H' (1 hour)
        logger.info(f"Resampling trades to {pandas_timeframe} timeframe...")
        ohlc_df = trades_df['price'].resample(pandas_timeframe).ohlc()

        if ohlc_df.empty:
            logger.info("OHLC data is empty after resampling (no trades in any interval).")
            return FootprintChartDataResponse(exchange=exchange, symbol=symbol, timeframe=timeframe_str, bars=[])

        footprint_bars: List[FootprintBar] = []

        logger.info(f"Aggregating trades into footprint bars for {len(ohlc_df)} candles...")
        for bar_timestamp, ohlc_data in ohlc_df.iterrows():
            if pd.isna(ohlc_data['open']): # Skip bars with no trades (NaN open)
                continue

            # bar_timestamp is the start of the interval (from resample)
            bar_start_time = bar_timestamp.to_pydatetime() # Convert pandas Timestamp to python datetime
            bar_end_time = bar_start_time + timeframe_delta

            # Filter trades belonging to this specific bar from the original DataFrame
            # Ensure timezone consistency: bar_start_time is now timezone-aware (UTC)
            bar_trades_df = trades_df[(trades_df.index >= bar_start_time) & (trades_df.index < bar_end_time)]

            if bar_trades_df.empty:
                continue # Should not happen if ohlc_data was valid, but as a safeguard

            price_level_aggregation: Dict[float, Dict[str, float]] = defaultdict(lambda: {'bid_volume': 0.0, 'ask_volume': 0.0})

            for _, trade_row in bar_trades_df.iterrows():
                price = trade_row['price']
                volume = trade_row['volume']
                aggressor = trade_row['aggressor_side'] # Already lowercased from DB or ingestion

                if aggressor == 'buy': # Buyer aggressor -> hit the Ask
                    price_level_aggregation[price]['ask_volume'] += volume
                elif aggressor == 'sell': # Seller aggressor -> hit the Bid
                    price_level_aggregation[price]['bid_volume'] += volume

            bar_price_levels: List[FootprintPriceLevel] = []
            bar_total_volume = 0.0
            bar_total_delta = 0.0

            # Sort price levels for consistent output
            sorted_prices = sorted(price_level_aggregation.keys())

            for price in sorted_prices:
                agg_data = price_level_aggregation[price]
                bid_vol = agg_data['bid_volume']
                ask_vol = agg_data['ask_volume']
                delta = ask_vol - bid_vol # Positive delta: more aggressive buying at this price
                total_vol_at_price = bid_vol + ask_vol

                bar_price_levels.append(FootprintPriceLevel(
                    price=price,
                    bid_volume=bid_vol,
                    ask_volume=ask_vol,
                    delta=delta,
                    total_volume=total_vol_at_price
                ))
                bar_total_volume += total_vol_at_price
                bar_total_delta += delta

            footprint_bars.append(FootprintBar(
                timestamp=bar_start_time, # Ensure this is UTC datetime
                open=ohlc_data['open'],
                high=ohlc_data['high'],
                low=ohlc_data['low'],
                close=ohlc_data['close'],
                total_volume=bar_total_volume,
                total_delta=bar_total_delta,
                price_levels=bar_price_levels # Already sorted by price
            ))

        logger.info(f"Generated {len(footprint_bars)} footprint bars.")
        return FootprintChartDataResponse(
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe_str,
            bars=footprint_bars
        )

# Example of how to handle HTTPException if service raises it, though usually done in endpoint
from fastapi import HTTPException # For type hinting or direct use if needed here
