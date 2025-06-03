import logging
from sqlalchemy.orm import Session # FootprintService needs it
from datetime import datetime, time # time for daily reset logic
"""
Service layer for calculating various delta-based market analysis metrics.

This service provides methods for:
- Cumulative Volume Delta (CVD).
- Advanced delta metrics like Delta Volume Pressure Ratio (DVPR)
  and Delta Moving Average Rate of Change/Value (DMRV).

It relies on FootprintService to obtain underlying bar data (OHLC, total delta, total volume).
"""
import logging
from datetime import datetime, time, timedelta # Added time, timedelta
from typing import List

import pandas as pd # For DataFrame operations
from sqlalchemy.orm import Session # Required by FootprintService dependency

from backend.app.models.delta_analysis_models import ( # Corrected import path
    AdvancedDeltaMetricsResponse,
    CVDChartDataResponse,
    CVDDataPoint,
    DMRVDataPoint,
    DVPRDataPoint,
)
from backend.app.services.footprint_service import FootprintService
from backend.app.utils.technical_analysis_utils import calculate_atr
from backend.app.utils.time_utils import parse_timeframe_to_timedelta

logger = logging.getLogger(__name__)

# Define a small epsilon for float comparisons, especially for division by zero checks
FLOAT_EPSILON_DA = 1e-9 # DA for Delta Analysis

class DeltaAnalysisService:
    """
    Service class for calculating delta-based market analysis metrics.
    """

    def get_cvd_data(
        self,
        db: Session,
        footprint_service: FootprintService,
        exchange: str,
        symbol: str,
        timeframe_str: str,
        start_dt: datetime,
        end_dt: datetime,
        reset_condition: str = "none"
    ) -> CVDChartDataResponse:
        """
        Calculates Cumulative Volume Delta (CVD) for a given market and period.

        Args:
            db: SQLAlchemy database session (passed to footprint_service).
            footprint_service: Instance of FootprintService to get bar data.
            exchange: Exchange name.
            symbol: Trading symbol.
            timeframe_str: Timeframe of the underlying bars (e.g., "1m", "5m").
            start_dt: Start datetime (UTC) for the data range.
            end_dt: End datetime (UTC) for the data range.
            reset_condition: When to reset CVD accumulation ("none" or "daily").

        Returns:
            CVDChartDataResponse containing the list of CVD data points.

        Raises:
            RuntimeError: If underlying bar data cannot be retrieved.
            ValueError: If timeframe string is invalid (propagated from utils).
        """
        logger.info(
            f"Calculating CVD for {exchange.lower()}/{symbol.lower()}, Timeframe: {timeframe_str}, "
            f"Range: {start_dt} to {end_dt}, Reset: {reset_condition}"
        )

        try:
            footprint_data = footprint_service.get_footprint_data(
                db=db, exchange=exchange, symbol=symbol,
                timeframe_str=timeframe_str, start_dt=start_dt, end_dt=end_dt
            )
        except Exception as e: # Catch errors from footprint_service (e.g., DB or ValueErrors)
            logger.error(f"Error getting footprint data for CVD calculation: {e}", exc_info=True)
            raise RuntimeError(f"Failed to retrieve underlying bar data for CVD: {str(e)}")

        if not footprint_data.bars:
            logger.info("No bars found from footprint_service to calculate CVD.")
            return CVDChartDataResponse(
                exchange=exchange.lower(), symbol=symbol.lower(), timeframe=timeframe_str,
                reset_condition=reset_condition, cvd_points=[]
            )

        # FootprintService should return bars sorted by timestamp. If not guaranteed, sort here.
        # sorted_bars = sorted(footprint_data.bars, key=lambda b: b.timestamp)
        # Assuming fp_data.bars is already sorted.

        cvd_points: List[CVDDataPoint] = []
        current_cvd = 0.0
        last_date_for_reset = None

        if reset_condition == "daily" and footprint_data.bars:
            last_date_for_reset = footprint_data.bars[0].timestamp.date()

        for bar in footprint_data.bars: # Use directly if already sorted
            bar_timestamp = bar.timestamp
            bar_delta = bar.total_delta

            if reset_condition == "daily":
                current_bar_date = bar_timestamp.date()
                if last_date_for_reset and current_bar_date != last_date_for_reset:
                    logger.debug(f"CVD daily reset: New day {current_bar_date} from {last_date_for_reset}. CVD reset from {current_cvd:.2f} to 0.")
                    current_cvd = 0.0
                last_date_for_reset = current_bar_date

            current_cvd += bar_delta
            cvd_points.append(CVDDataPoint(timestamp=bar_timestamp, cvd_value=current_cvd))

        logger.info(f"Successfully calculated {len(cvd_points)} CVD points for {exchange.lower()}/{symbol.lower()}.")
        return CVDChartDataResponse(
            exchange=exchange.lower(),
            symbol=symbol.lower(),
            timeframe=timeframe_str,
            reset_condition=reset_condition,
            cvd_points=cvd_points
        )

    def get_advanced_delta_metrics(
        self,
        db: Session,
        footprint_service: FootprintService,
        exchange: str,
        symbol: str,
        timeframe_str: str,
        start_dt: datetime,
        end_dt: datetime,
        atr_period: int = 14,
        dmrv_short_period: int = 5,
        dmrv_long_period: int = 10
    ) -> AdvancedDeltaMetricsResponse:
        """
        Calculates advanced delta metrics: DVPR and DMRV.

        Args:
            db: SQLAlchemy database session.
            footprint_service: Instance of FootprintService.
            exchange: Exchange name.
            symbol: Trading symbol.
            timeframe_str: Timeframe for bars.
            start_dt: Start datetime (UTC) for the response data range.
            end_dt: End datetime (UTC) for the response data range.
            atr_period: Period for ATR calculation.
            dmrv_short_period: Short MA period for DMRV delta.
            dmrv_long_period: Long MA period for DMRV delta.

        Returns:
            AdvancedDeltaMetricsResponse containing lists of DVPR and DMRV data points.

        Raises:
            ValueError: If timeframe string is invalid or MA periods are illogical.
            RuntimeError: If underlying bar data cannot be retrieved.
        """
        logger.info(
            f"Calculating Advanced Delta Metrics for {exchange.lower()}/{symbol.lower()}, TF: {timeframe_str}, "
            f"Range: {start_dt}-{end_dt}, ATR: {atr_period}, DMRV: {dmrv_short_period}/{dmrv_long_period}"
        )

        if dmrv_short_period >= dmrv_long_period:
            msg = "DMRV short MA period must be less than long MA period."
            logger.error(msg)
            raise ValueError(msg)

        # 1. Calculate lookback duration needed for ATR and MAs
        timeframe_delta_obj = parse_timeframe_to_timedelta(timeframe_str) # Can raise ValueError

        required_lookback_bars = max(atr_period, dmrv_long_period) + 5 # Buffer for stable calculation
        lookback_duration = timeframe_delta_obj * required_lookback_bars
        extended_start_dt = start_dt - lookback_duration
        logger.debug(f"Data fetch range: Original start={start_dt}, Extended start for lookback={extended_start_dt}")

        # 2. Get footprint bars (OHLC, total_delta, total_volume)
        try:
            fp_data = footprint_service.get_footprint_data(
                db, exchange, symbol, timeframe_str, extended_start_dt, end_dt
            )
        except Exception as e: # Catch errors from footprint_service
            logger.error(f"Error getting footprint data for Advanced Delta Metrics: {e}", exc_info=True)
            raise RuntimeError(f"Failed to retrieve underlying bar data for Advanced Delta Metrics: {str(e)}")

        if not fp_data.bars:
            logger.info("No bars from footprint_service for Advanced Delta Metrics calculation.")
            return AdvancedDeltaMetricsResponse(
                exchange=exchange.lower(), symbol=symbol.lower(), timeframe=timeframe_str,
                dvpr_points=[], dmrv_points=[]
            )

        # 3. Convert to Pandas DataFrame
        bars_list_of_dicts = [
            b.model_dump(include={'timestamp', 'open', 'high', 'low', 'close', 'total_volume', 'total_delta'})
            for b in fp_data.bars
        ]
        bars_df = pd.DataFrame(bars_list_of_dicts)

        if bars_df.empty:
            logger.info("DataFrame empty after converting footprint bars (unexpected).")
            return AdvancedDeltaMetricsResponse(
                exchange=exchange.lower(), symbol=symbol.lower(), timeframe=timeframe_str,
                dvpr_points=[], dmrv_points=[]
            )

        bars_df['timestamp'] = pd.to_datetime(bars_df['timestamp'], utc=True)
        bars_df.set_index('timestamp', inplace=True)
        bars_df.sort_index(inplace=True) # Crucial for time-series calculations

        # 4. Calculate ATR
        bars_df['atr'] = calculate_atr(bars_df, period=atr_period)

        # 5. Calculate DVPR = BarDelta / (BarVolume * ATR)
        bars_df['dvpr'] = bars_df.apply(
            lambda x: x['total_delta'] / (x['total_volume'] * x['atr'])
            if x['total_volume'] > FLOAT_EPSILON_DA and x['atr'] > FLOAT_EPSILON_DA else None,
            axis=1
        )

        # 6. Calculate DMRV
        bars_df['delta_sma_short'] = bars_df['total_delta'].rolling(window=dmrv_short_period, min_periods=dmrv_short_period).mean()
        bars_df['delta_sma_long'] = bars_df['total_delta'].rolling(window=dmrv_long_period, min_periods=dmrv_long_period).mean()
        bars_df['dmrv'] = bars_df['delta_sma_short'] - bars_df['delta_sma_long']

        # 7. Filter DataFrame back to the original requested date range
        result_df = bars_df[bars_df.index >= pd.Timestamp(start_dt, tz='UTC')] # Ensure start_dt is tz-aware for comparison

        if result_df.empty:
            logger.info("Result DataFrame empty after filtering for original date range (no data within requested window after lookback).")
            return AdvancedDeltaMetricsResponse(
                exchange=exchange.lower(), symbol=symbol.lower(), timeframe=timeframe_str,
                dvpr_points=[], dmrv_points=[]
            )

        dvpr_points: List[DVPRDataPoint] = []
        dmrv_points: List[DMRVDataPoint] = []

        for ts_pd, row in result_df.iterrows():
            ts_dt = ts_pd.to_pydatetime() # Convert pandas Timestamp to python datetime
            dvpr_points.append(DVPRDataPoint(
                timestamp=ts_dt,
                dvpr_value=row.get('dvpr') if pd.notna(row.get('dvpr')) else None,
                bar_delta=row['total_delta'],
                bar_volume=row['total_volume'],
                bar_atr=row.get('atr') if pd.notna(row.get('atr')) else None
            ))
            dmrv_points.append(DMRVDataPoint(
                timestamp=ts_dt,
                short_delta_ma=row.get('delta_sma_short') if pd.notna(row.get('delta_sma_short')) else None,
                long_delta_ma=row.get('delta_sma_long') if pd.notna(row.get('delta_sma_long')) else None,
                dmrv_value=row.get('dmrv') if pd.notna(row.get('dmrv')) else None
            ))

        logger.info(f"Successfully calculated {len(dvpr_points)} DVPR and {len(dmrv_points)} DMRV points for {exchange.lower()}/{symbol.lower()}.")
        return AdvancedDeltaMetricsResponse(
            exchange=exchange.lower(), symbol=symbol.lower(), timeframe=timeframe_str,
            dvpr_points=dvpr_points, dmrv_points=dmrv_points
        )
