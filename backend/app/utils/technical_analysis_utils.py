import pandas as pd
from typing import List # Not used in this snippet but often useful in utils

def calculate_atr(ohlc_df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates Average True Range (ATR).
    :param ohlc_df: Pandas DataFrame with columns 'high', 'low', 'close'.
                    It's assumed to be sorted by time in ascending order.
    :param period: The period for ATR calculation.
    :return: Pandas Series with ATR values.
    """
    if ohlc_df.empty:
        return pd.Series(dtype='float64', index=ohlc_df.index) # Return empty series with same index type

    required_cols = ['high', 'low', 'close']
    if not all(col in ohlc_df.columns for col in required_cols):
        missing_cols = [col for col in required_cols if col not in ohlc_df.columns]
        # In a real app, might raise ValueError or log a warning
        # For now, returning empty series if essential columns are missing
        # print(f"ATR calculation missing columns: {missing_cols}") # Or use logger
        return pd.Series(dtype='float64', index=ohlc_df.index)

    # Calculate True Range (TR)
    high_low = ohlc_df['high'] - ohlc_df['low']

    # Shift close for previous day's close calculation. Fill first NaN with a value that won't skew TR (e.g., first 'high' or 'low')
    # This is important to avoid NaNs in TR if using .abs() directly.
    # A common approach is to use the first available 'close' for the first TR calculation,
    # or to ensure enough data exists prior to the period of interest.
    # Pandas .shift(1) will introduce a NaN at the first row.
    close_prev = ohlc_df['close'].shift(1)

    high_close_prev = (ohlc_df['high'] - close_prev).abs()
    low_close_prev = (ohlc_df['low'] - close_prev).abs()

    # TR is the greatest of these three
    tr_df = pd.concat([high_low, high_close_prev, low_close_prev], axis=1)
    true_range = tr_df.max(axis=1, skipna=False) # Ensure NaNs propagate if all inputs are NaN for a row

    # Calculate ATR using Exponential Moving Average (EMA)
    # The first ATR value (after 'period' TR values) is a simple average of TRs.
    # Subsequent ATRs = ((Previous ATR * (period - 1)) + Current TR) / period
    # Pandas ewm with alpha=1/period and adjust=False closely mimics this.
    # min_periods=period ensures that we only get ATR values after enough data.
    atr = true_range.ewm(alpha=1.0/period, adjust=False, min_periods=period).mean()

    # Alternative: Simple Moving Average of TR (less common for standard ATR)
    # atr = true_range.rolling(window=period).mean()

    return atr

# Example usage (for testing, can be removed)
if __name__ == '__main__':
    data = {
        'timestamp': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05',
                                     '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10',
                                     '2023-01-11', '2023-01-12', '2023-01-13', '2023-01-14', '2023-01-15']),
        'high': [10, 11, 10.5, 12, 12.5, 13, 13.5, 12.8, 13.2, 14, 14.5, 15, 14.8, 15.2, 15.5],
        'low':  [9, 10, 9.5, 10.2, 11.5, 12, 12.5, 11.8, 12.2, 13, 13.5, 14, 13.8, 14.2, 14.5],
        'close':[9.5, 10.5, 10, 11.8, 12, 12.8, 13, 12.2, 13, 13.8, 14, 14.8, 14.2, 15, 15.2]
    }
    sample_df = pd.DataFrame(data)
    sample_df.set_index('timestamp', inplace=True)

    atr_values = calculate_atr(sample_df, period=5)
    print("Sample OHLC Data with ATR (period=5):")
    print(pd.concat([sample_df, atr_values.rename('atr')], axis=1))

    atr_10 = calculate_atr(sample_df, period=10)
    print("\nATR (period=10):")
    print(pd.concat([sample_df, atr_10.rename('atr_10')], axis=1))
