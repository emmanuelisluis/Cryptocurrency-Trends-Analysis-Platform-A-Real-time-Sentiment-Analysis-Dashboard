import logging
from sqlalchemy.orm import Session
# from sqlalchemy import func # Not used in the provided snippet, but often useful for DB aggregations
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import pandas as pd

from backend.app.db.models import TradeDB # Corrected import path
from backend.app.models.volume_profile_models import VolumeProfileLevel, VolumeProfileData
# from backend.app.core.config import settings # Uncomment if settings (e.g., VA_PERCENTAGE) are used

logger = logging.getLogger(__name__)

DEFAULT_VA_PERCENTAGE = 0.70 # Default Value Area percentage

class VolumeProfileService:
    def _calculate_poc_and_va(
        self,
        levels_df: pd.DataFrame, # Expects columns 'price', 'total_volume'
        total_profile_volume: float,
        va_percentage: float = DEFAULT_VA_PERCENTAGE
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:

        if levels_df.empty or total_profile_volume == 0:
            logger.debug("Levels DataFrame is empty or total profile volume is zero. Cannot calculate POC/VA.")
            return None, None, None, None

        try:
            # Point of Control (POC)
            # Ensure 'total_volume' is numeric, handle potential NaNs if any from grouping
            levels_df['total_volume'] = pd.to_numeric(levels_df['total_volume'], errors='coerce').fillna(0)

            poc_idx = levels_df['total_volume'].idxmax()
            poc_level_series = levels_df.loc[poc_idx]
            poc_price = float(poc_level_series['price'])
            poc_volume = float(poc_level_series['total_volume'])
            logger.debug(f"Calculated POC: Price={poc_price}, Volume={poc_volume}")

            # Value Area (VA)
            # Sort by volume DESC to start from POC, then by price ASC as tie-breaker
            # This ensures POC is the first level considered for VA.
            sorted_by_volume_df = levels_df.sort_values(by=['total_volume', 'price'], ascending=[False, True])

            cumulative_volume_for_va = 0.0
            va_prices = [] # Store prices included in VA

            target_va_volume = total_profile_volume * va_percentage
            logger.debug(f"Target VA volume ({va_percentage*100}%): {target_va_volume}")

            for _, row in sorted_by_volume_df.iterrows():
                if cumulative_volume_for_va >= target_va_volume:
                    if row['price'] != poc_price: # Try to add the other side of POC if it makes VA more continuous
                        # This logic can get complex. Simplified: just break once target met.
                        # A more advanced VA might try to keep it somewhat contiguous around POC.
                        pass # For now, simple break.
                    break

                va_prices.append(float(row['price']))
                cumulative_volume_for_va += float(row['total_volume'])

            if not va_prices:
                logger.debug("VA calculation resulted in no levels (e.g., only one price level). VA High/Low will be POC price.")
                return poc_price, poc_volume, poc_price, poc_price # VA is just the POC level

            value_area_low = min(va_prices)
            value_area_high = max(va_prices)
            logger.debug(f"Calculated VA: Low={value_area_low}, High={value_area_high}, with {len(va_prices)} levels and volume {cumulative_volume_for_va}")

            return poc_price, poc_volume, value_area_low, value_area_high
        except Exception as e:
            logger.error(f"Error during POC/VA calculation: {e}", exc_info=True)
            return None, None, None, None


    def get_volume_profile(
        self,
        db: Session,
        exchange: str,
        symbol: str,
        start_dt: datetime,
        end_dt: datetime,
        profile_type: str = "range", # Default or passed from endpoint
        price_tick_size: Optional[float] = None
    ) -> VolumeProfileData:

        logger.info(f"Fetching trades for Volume Profile: {exchange}/{symbol}, Type: {profile_type}, Range: {start_dt} - {end_dt}, Tick: {price_tick_size}")

        # 1. Fetch trades from DB
        query = db.query(TradeDB.price, TradeDB.volume).filter(
            TradeDB.exchange == exchange.lower(),
            TradeDB.symbol == symbol.lower(),
            TradeDB.timestamp >= start_dt,
            TradeDB.timestamp < end_dt # Exclusive end_dt
        )

        try:
            trades_df = pd.read_sql(query.statement, db.bind)
        except Exception as e:
            logger.error(f"Database error fetching trades for volume profile: {e}", exc_info=True)
            # Consider raising a specific DB error or returning empty profile
            raise RuntimeError(f"Database error fetching trades: {e}")


        if trades_df.empty:
            logger.info("No trades found for the given criteria to build volume profile.")
            return VolumeProfileData(profile_type=profile_type, start_time_utc=start_dt, end_time_utc=end_dt, levels=[])

        # 2. Optional: Group prices by tick size if raw price levels are too granular
        if price_tick_size and price_tick_size > 0:
            logger.debug(f"Grouping prices by tick size: {price_tick_size}")
            trades_df['price'] = (trades_df['price'] / price_tick_size).round() * price_tick_size

        # 3. Aggregate volume at each price level
        volume_at_price_df = trades_df.groupby('price')['volume'].sum().reset_index()
        volume_at_price_df.rename(columns={'volume': 'total_volume'}, inplace=True)

        if volume_at_price_df.empty: # Should not happen if trades_df was not empty, but safeguard
            logger.info("Volume at price is empty after grouping (unexpected).")
            return VolumeProfileData(profile_type=profile_type, start_time_utc=start_dt, end_time_utc=end_dt, levels=[])

        total_profile_volume = float(volume_at_price_df['total_volume'].sum())
        logger.debug(f"Total profile volume: {total_profile_volume}")

        # 4. Calculate POC and VA
        poc_price, poc_volume, va_low, va_high = self._calculate_poc_and_va(
            volume_at_price_df.copy(), # Pass a copy to avoid modification issues if any
            total_profile_volume,
            va_percentage=DEFAULT_VA_PERCENTAGE
        )

        # 5. Prepare levels for response, sorted by price
        profile_levels = [
            VolumeProfileLevel(price=float(row['price']), total_volume=float(row['total_volume']))
            for _, row in volume_at_price_df.sort_values(by='price').iterrows()
        ]

        return VolumeProfileData(
            profile_type=profile_type,
            start_time_utc=start_dt,
            end_time_utc=end_dt,
            levels=profile_levels,
            point_of_control_price=poc_price,
            point_of_control_volume=poc_volume,
            value_area_high=va_high,
            value_area_low=va_low,
            total_profile_volume=total_profile_volume
        )
