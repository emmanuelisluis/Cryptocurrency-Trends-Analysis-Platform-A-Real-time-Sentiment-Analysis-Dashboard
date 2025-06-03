import logging
from sqlalchemy.orm import Session
# from sqlalchemy import func # Not used in the provided snippet, but often useful for DB aggregations
from datetime import datetime, timedelta
"""
Service layer for calculating Volume Profile data.

This service fetches raw trade data for a given period and aggregates it
to build a volume profile, identifying the Point of Control (POC) and Value Area (VA).
"""
import logging
from datetime import datetime, timedelta # timedelta not used directly, but good for context
from typing import List, Optional, Tuple

import pandas as pd # Assumed to be installed
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException # For raising errors to be handled by API layer

from backend.app.db.models import TradeDB
from backend.app.models.volume_profile_models import VolumeProfileLevel, VolumeProfileData
from backend.app.core.config import settings # For VA_PERCENTAGE or other settings

logger = logging.getLogger(__name__)

# Default Value Area percentage, can be moved to config if needed
DEFAULT_VA_PERCENTAGE = getattr(settings, 'VOLUME_PROFILE_VA_PERCENTAGE', 0.70)
FLOAT_EPSILON_VP = 1e-9 # Small epsilon for float comparisons, especially for division by zero


class VolumeProfileService:
    """
    Service class for calculating volume profile data including POC and VA.
    """

    def _calculate_poc_and_va(
        self,
        levels_df: pd.DataFrame,
        total_profile_volume: float,
        va_percentage: float = DEFAULT_VA_PERCENTAGE
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """
        Calculates Point of Control (POC) and Value Area (VA) from volume levels.

        Args:
            levels_df: DataFrame with 'price' and 'total_volume' columns.
            total_profile_volume: Total volume across all price levels in the profile.
            va_percentage: Percentage of total volume to be included in the Value Area.

        Returns:
            A tuple containing: (poc_price, poc_volume, value_area_low, value_area_high).
            Returns (None, None, None, None) if calculation is not possible.
        """
        if levels_df.empty or total_profile_volume < FLOAT_EPSILON_VP:
            logger.debug("Levels DataFrame is empty or total profile volume is near zero. Cannot calculate POC/VA.")
            return None, None, None, None

        try:
            # Ensure 'total_volume' is numeric and handle potential NaNs
            levels_df['total_volume'] = pd.to_numeric(levels_df['total_volume'], errors='coerce').fillna(0)

            # Point of Control (POC): Price level with the highest volume
            poc_idx = levels_df['total_volume'].idxmax() # Index of the max volume row
            poc_level_series = levels_df.loc[poc_idx]
            poc_price = float(poc_level_series['price'])
            poc_volume = float(poc_level_series['total_volume'])
            logger.debug(f"Calculated POC: Price={poc_price}, Volume={poc_volume}")

            # Value Area (VA) Calculation:
            # 1. Sort levels by volume (descending) to find highest volume levels first.
            #    Break ties by price (ascending) - though usually not critical for VA.
            sorted_by_volume_df = levels_df.sort_values(by=['total_volume', 'price'], ascending=[False, True])

            cumulative_volume_for_va = 0.0
            va_prices: List[float] = [] # Store prices included in the VA

            target_va_volume = total_profile_volume * va_percentage
            logger.debug(f"Target VA volume ({va_percentage*100}% of {total_profile_volume}): {target_va_volume}")

            # Iterate through sorted levels, adding to VA until target volume percentage is met
            for _, row in sorted_by_volume_df.iterrows():
                if cumulative_volume_for_va >= target_va_volume:
                    # Optimization: if current row's volume is much smaller than what's needed to hit target,
                    # and we've already included POC, we might stop to make VA more compact.
                    # For now, simple break once target volume is achieved.
                    break

                va_prices.append(float(row['price']))
                cumulative_volume_for_va += float(row['total_volume'])

            if not va_prices: # Should not happen if POC was found and has volume
                logger.warning("VA calculation resulted in no price levels. Defaulting VA to POC level.")
                return poc_price, poc_volume, poc_price, poc_price

            value_area_low = min(va_prices)
            value_area_high = max(va_prices)
            logger.debug(
                f"Calculated VA: Low={value_area_low}, High={value_area_high} "
                f"with {len(va_prices)} price levels, covering {cumulative_volume_for_va:.2f} volume."
            )

            return poc_price, poc_volume, value_area_low, value_area_high
        except Exception as e:
            logger.error(f"Error during POC/VA calculation: {e}", exc_info=True)
            return None, None, None, None # Return Nones on error


    def get_volume_profile(
        self,
        db: Session,
        exchange: str,
        symbol: str,
        start_dt: datetime,
        end_dt: datetime,
        profile_type: str = "range",
        price_tick_size: Optional[float] = None
    ) -> VolumeProfileData:
        """
        Generates volume profile data for a given market, time range, and optional price tick grouping.

        Args:
            db: SQLAlchemy database session.
            exchange: Exchange name.
            symbol: Trading symbol.
            start_dt: Start datetime (UTC) for data fetching.
            end_dt: End datetime (UTC) for data fetching.
            profile_type: Type of profile being generated (e.g., "daily", "range").
            price_tick_size: Optional. If provided, trade prices are grouped by this tick size.

        Returns:
            VolumeProfileData Pydantic model instance.

        Raises:
            HTTPException: If database errors occur during trade fetching.
        """
        logger.info(
            f"Generating Volume Profile: {exchange.lower()}/{symbol.lower()}, Type: {profile_type}, "
            f"Range: {start_dt} - {end_dt}, Tick Grouping: {price_tick_size or 'None'}"
        )

        # 1. Fetch trades from DB (only price and volume are needed for basic VP)
        query = db.query(TradeDB.price, TradeDB.volume).filter(
            TradeDB.exchange == exchange.lower(),
            TradeDB.symbol == symbol.lower(),
            TradeDB.timestamp >= start_dt,
            TradeDB.timestamp < end_dt # end_dt is exclusive
        )

        try:
            trades_df = pd.read_sql(query.statement, db.bind)
            logger.debug(f"Fetched {len(trades_df)} trades for volume profile calculation.")
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching trades for volume profile: {e}", exc_info=True)
            raise HTTPException(status_code=503, detail=f"Database error fetching trades: {str(e)}")
        except Exception as e: # Other potential errors with read_sql
            logger.error(f"Unexpected error reading trades into DataFrame for VP: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Unexpected error reading trades: {str(e)}")


        if trades_df.empty:
            logger.info("No trades found for the given criteria; returning empty volume profile.")
            return VolumeProfileData(profile_type=profile_type, start_time_utc=start_dt, end_time_utc=end_dt, levels=[])

        # 2. Optional: Group prices by tick size if raw price levels are too granular
        if price_tick_size and price_tick_size > FLOAT_EPSILON_VP:
            logger.debug(f"Grouping prices by tick size: {price_tick_size}")
            # Round prices to the nearest tick size increment
            trades_df['price'] = (trades_df['price'] / price_tick_size).round() * price_tick_size

        # 3. Aggregate volume at each price level
        volume_at_price_df = trades_df.groupby('price')['volume'].sum().reset_index()
        volume_at_price_df.rename(columns={'volume': 'total_volume'}, inplace=True)

        if volume_at_price_df.empty:
            logger.info("Volume at price DataFrame is empty after grouping (e.g., all trades had zero volume, or only one price after grouping).")
            return VolumeProfileData(profile_type=profile_type, start_time_utc=start_dt, end_time_utc=end_dt, levels=[])

        total_profile_volume = float(volume_at_price_df['total_volume'].sum())
        logger.debug(f"Total profile volume calculated: {total_profile_volume}")

        # 4. Calculate POC and VA
        poc_price, poc_volume, va_low, va_high = self._calculate_poc_and_va(
            volume_at_price_df.copy(), # Pass a copy to avoid modifying the original df in the method
            total_profile_volume,
            # va_percentage can be sourced from settings if made configurable
            va_percentage=getattr(settings, 'VOLUME_PROFILE_VA_PERCENTAGE', DEFAULT_VA_PERCENTAGE)
        )

        # 5. Prepare levels for response, ensuring they are sorted by price
        profile_levels_list = [
            VolumeProfileLevel(price=float(row['price']), total_volume=float(row['total_volume']))
            for _, row in volume_at_price_df.sort_values(by='price').iterrows() # Ensure sorted by price
        ]

        logger.info(f"Volume profile generated for {exchange.lower()}/{symbol.lower()} with {len(profile_levels_list)} price levels.")
        return VolumeProfileData(
            profile_type=profile_type,
            start_time_utc=start_dt,
            end_time_utc=end_dt,
            levels=profile_levels_list,
            point_of_control_price=poc_price,
            point_of_control_volume=poc_volume,
            value_area_high=va_high,
            value_area_low=va_low,
            total_profile_volume=total_profile_volume
        )
