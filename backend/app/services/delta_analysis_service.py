import logging
from sqlalchemy.orm import Session # FootprintService needs it
from datetime import datetime, time # time for daily reset logic
from typing import List
import pandas as pd # For DataFrame operations
from datetime import timedelta # For lookback calculation

from backend.app.services.footprint_service import FootprintService
from backend.app.models.delta_analysis_models import (
    CVDDataPoint, CVDChartDataResponse,
    DVPRDataPoint, DMRVDataPoint, AdvancedDeltaMetricsResponse # New models
)
from backend.app.utils.technical_analysis_utils import calculate_atr # ATR utility
from backend.app.utils.time_utils import parse_timeframe_to_timedelta # For lookback

logger = logging.getLogger(__name__)

class DeltaAnalysisService:
    def get_cvd_data(
        self,
        db: Session,
        footprint_service: FootprintService, # Inject FootprintService
        exchange: str,
        symbol: str,
        timeframe_str: str, # Timeframe for bars (e.g., "1m", "5m")
        start_dt: datetime,
        end_dt: datetime,
        reset_condition: str = "none" # "none", "daily"
    ) -> CVDChartDataResponse:

        logger.info(f"Calculating CVD for {exchange}/{symbol}, Timeframe: {timeframe_str}, Range: {start_dt}-{end_dt}, Reset: {reset_condition}")

        # 1. Get footprint bars (which contain total_delta per bar)
        # This reuses the logic from FootprintService to get bars with their total_delta.
        try:
            footprint_data = footprint_service.get_footprint_data(
                db=db,
                exchange=exchange,
                symbol=symbol,
                timeframe_str=timeframe_str,
                start_dt=start_dt,
                end_dt=end_dt
            )
        except Exception as e:
            logger.error(f"Error getting footprint data for CVD calculation: {e}", exc_info=True)
            # Depending on how specific the error from footprint_service is, re-raise or wrap
            raise RuntimeError(f"Failed to retrieve underlying bar data for CVD: {str(e)}")


        if not footprint_data.bars:
            logger.info("No bars found from footprint_service to calculate CVD.")
            return CVDChartDataResponse(
                exchange=exchange, symbol=symbol, timeframe=timeframe_str,
                reset_condition=reset_condition, cvd_points=[]
            )

        # Sort bars by timestamp to ensure correct CVD accumulation
        # FootprintService should already return them sorted, but an extra sort doesn't hurt.
        sorted_bars = sorted(footprint_data.bars, key=lambda b: b.timestamp)

        cvd_points: List[CVDDataPoint] = []
        current_cvd = 0.0
        # last_date is used to track day changes for 'daily' reset_condition
        # It should be initialized based on the first bar's date or None
        last_date = None
        if reset_condition == "daily" and sorted_bars:
            # Initialize last_date with the date of the first bar to avoid resetting on the very first bar.
            last_date = sorted_bars[0].timestamp.date()


        for bar in sorted_bars:
            bar_timestamp = bar.timestamp # This is the start time of the bar
            bar_delta = bar.total_delta

            if reset_condition == "daily":
                current_bar_date = bar_timestamp.date()
                if last_date and current_bar_date != last_date:
                    logger.debug(f"CVD daily reset triggered: {current_bar_date} != {last_date}. Resetting CVD from {current_cvd} to 0.")
                    current_cvd = 0.0 # Reset CVD at the start of a new day
                last_date = current_bar_date

            current_cvd += bar_delta
            # The timestamp for CVDDataPoint should align with the bar's timestamp (usually close/end of bar)
            # FootprintBar.timestamp is the start of the bar.
            # For CVD, it's common to plot against the bar's end time or its identifying timestamp.
            # Let's use the bar.timestamp (start of bar) for consistency with how bars are identified.
            cvd_points.append(CVDDataPoint(timestamp=bar_timestamp, cvd_value=current_cvd))

        logger.info(f"Successfully calculated {len(cvd_points)} CVD points.")
        return CVDChartDataResponse(
            exchange=exchange,
            symbol=symbol,
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

        logger.info(f"Calculating Advanced Delta Metrics for {exchange}/{symbol}, Timeframe: {timeframe_str}, Range: {start_dt}-{end_dt}")

        # 1. Calculate lookback duration needed for ATR and MAs
        try:
            timeframe_delta_obj = parse_timeframe_to_timedelta(timeframe_str)
        except ValueError: # Handle invalid timeframe string from util
            logger.error(f"Invalid timeframe string for delta metrics: {timeframe_str}")
            raise # Re-raise to be caught by endpoint

        required_lookback_bars = max(atr_period, dmrv_long_period) + 5 # Add a buffer for stable calculation start
        lookback_duration = timeframe_delta_obj * required_lookback_bars
        extended_start_dt = start_dt - lookback_duration
        logger.debug(f"Original start: {start_dt}, Extended start for lookback: {extended_start_dt}")

        # 2. Get footprint bars (OHLC, total_delta, total_volume)
        try:
            fp_data = footprint_service.get_footprint_data(db, exchange, symbol, timeframe_str, extended_start_dt, end_dt)
        except Exception as e:
            logger.error(f"Error getting footprint data for Advanced Delta Metrics: {e}", exc_info=True)
            raise RuntimeError(f"Failed to retrieve underlying bar data for Advanced Delta Metrics: {str(e)}")


        if not fp_data.bars:
            logger.info("No bars found from footprint_service for Advanced Delta Metrics.")
            return AdvancedDeltaMetricsResponse(exchange=exchange, symbol=symbol, timeframe=timeframe_str, dvpr_points=[], dmrv_points=[])

        # 3. Convert to DataFrame for easier processing with Pandas
        # Ensure all necessary fields from FootprintBar model are included
        bars_list_of_dicts = [
            b.model_dump(include={'timestamp', 'open', 'high', 'low', 'close', 'total_volume', 'total_delta'})
            for b in fp_data.bars
        ]
        bars_df = pd.DataFrame(bars_list_of_dicts)

        if bars_df.empty: # Should be caught by fp_data.bars check, but as a safeguard
            logger.info("DataFrame empty after converting footprint bars.")
            return AdvancedDeltaMetricsResponse(exchange=exchange, symbol=symbol, timeframe=timeframe_str, dvpr_points=[], dmrv_points=[])

        bars_df['timestamp'] = pd.to_datetime(bars_df['timestamp'])
        bars_df.set_index('timestamp', inplace=True)
        bars_df.sort_index(inplace=True) # Ensure chronological order for MAs and ATR

        # 4. Calculate ATR
        bars_df['atr'] = calculate_atr(bars_df, period=atr_period)

        # 5. Calculate DVPR = BarDelta / (BarVolume * ATR)
        # Handle division by zero or NaN ATR/Volume
        bars_df['dvpr'] = bars_df.apply(
            lambda x: x['total_delta'] / (x['total_volume'] * x['atr'])
            if x['total_volume'] > 0.0000001 and x['atr'] > 0.0000001 else None, # Check for positive volume and ATR
            axis=1
        )

        # 6. Calculate DMRV (Delta Moving Average Rate of Change/Value)
        bars_df['delta_sma_short'] = bars_df['total_delta'].rolling(window=dmrv_short_period, min_periods=dmrv_short_period).mean()
        bars_df['delta_sma_long'] = bars_df['total_delta'].rolling(window=dmrv_long_period, min_periods=dmrv_long_period).mean()
        bars_df['dmrv'] = bars_df['delta_sma_short'] - bars_df['delta_sma_long']
        # Optional: DMRV velocity (diff)
        # bars_df['dmrv_velocity'] = bars_df['dmrv'].diff()

        # 7. Filter DataFrame back to the original requested date range (start_dt to end_dt)
        # This ensures calculations had enough prior data but response is for the requested window.
        # Note: Pandas index filtering with datetimes should be timezone-aware if original datetimes are.
        # start_dt and end_dt are assumed to be timezone-aware (UTC) from the endpoint.
        result_df = bars_df[bars_df.index >= start_dt]

        if result_df.empty:
            logger.info("Result DataFrame empty after filtering for original date range.")
            return AdvancedDeltaMetricsResponse(exchange=exchange, symbol=symbol, timeframe=timeframe_str, dvpr_points=[], dmrv_points=[])


        dvpr_points: List[DVPRDataPoint] = []
        dmrv_points: List[DMRVDataPoint] = []

        for ts, row in result_df.iterrows():
            # ts is already a datetime object (pandas Timestamp, which is fine)
            dvpr_points.append(DVPRDataPoint(
                timestamp=ts.to_pydatetime(), # Convert pandas Timestamp to python datetime
                dvpr_value=row.get('dvpr') if pd.notna(row.get('dvpr')) else None,
                bar_delta=row['total_delta'],
                bar_volume=row['total_volume'],
                bar_atr=row.get('atr') if pd.notna(row.get('atr')) else None
            ))
            dmrv_points.append(DMRVDataPoint(
                timestamp=ts.to_pydatetime(),
                short_delta_ma=row.get('delta_sma_short') if pd.notna(row.get('delta_sma_short')) else None,
                long_delta_ma=row.get('delta_sma_long') if pd.notna(row.get('delta_sma_long')) else None,
                dmrv_value=row.get('dmrv') if pd.notna(row.get('dmrv')) else None
            ))

        logger.info(f"Successfully calculated {len(dvpr_points)} DVPR and {len(dmrv_points)} DMRV points.")
        return AdvancedDeltaMetricsResponse(
            exchange=exchange, symbol=symbol, timeframe=timeframe_str,
            dvpr_points=dvpr_points, dmrv_points=dmrv_points
        )
