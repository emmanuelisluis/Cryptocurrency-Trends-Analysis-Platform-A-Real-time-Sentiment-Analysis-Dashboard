from datetime import timedelta
import re # For more robust parsing

def parse_timeframe_to_timedelta(timeframe: str) -> timedelta:
    """
    Parses a timeframe string (e.g., "1m", "5m", "1h", "1d") into a timedelta object.
    """
    match = re.match(r"(\d+)([mhdwsMy])", timeframe.lower()) # Added w, M, Y for week, month, year (approximate for M, Y)
    if not match:
        raise ValueError(f"Unsupported timeframe format: {timeframe}. Examples: '1m', '5H', '1D'.")

    value = int(match.group(1))
    unit = match.group(2)

    if unit == 'm': # minute
        return timedelta(minutes=value)
    elif unit == 'h': # hour
        return timedelta(hours=value)
    elif unit == 'd': # day
        return timedelta(days=value)
    elif unit == 'w': # week
        return timedelta(weeks=value)
    # Monthly/Yearly are more complex due to varying lengths.
    # For simplicity in aggregation, fixed days might be used, or rely on pandas period objects if more accuracy is needed.
    # This basic version provides an approximation.
    elif unit == 'M': # month (approx 30 days for delta, pandas handles actual month ends better)
        return timedelta(days=value * 30)
    elif unit == 'y': # year (approx 365 days for delta)
        return timedelta(days=value * 365)
    else:
        # Should not be reached if regex is correct and comprehensive
        raise ValueError(f"Unsupported timeframe unit: {unit} in {timeframe}")

def map_timeframe_to_pandas_freq(timeframe_str: str) -> str:
    """
    Maps a custom timeframe string (e.g., "1m", "5m", "1h") to a pandas frequency string.
    """
    # Ensure lowercase for matching
    tf_lower = timeframe_str.lower()

    if 'm' in tf_lower and not 'min' in tf_lower: # e.g., "1m", "5m", "15m"
        return tf_lower.replace('m', 'min')
    elif 'h' in tf_lower and not 'H' in tf_lower: # e.g., "1h", "4h"
        return tf_lower.upper() # Pandas uses 'H' for hours, e.g., "1H", "4H"
    elif 'd' in tf_lower and not 'D' in tf_lower: # e.g., "1d"
        return tf_lower.upper() # Pandas uses 'D' for days
    elif 'w' in tf_lower and not 'W' in tf_lower: # e.g., "1w"
        return tf_lower.upper() # Pandas uses 'W' for weeks
    # Add more mappings if needed (e.g. for months 'M', which is end of month frequency)

    # If already in a common pandas format or no specific rule, return as is
    # This might need more robust logic depending on the exact timeframe strings used.
    # For example, if you use "min" directly in your timeframe strings.
    if tf_lower.endswith('min') or tf_lower.endswith('H') or tf_lower.endswith('D') or tf_lower.endswith('W'):
        return timeframe_str # Assume already compatible if it ends like a pandas freq.

    # Fallback or raise error if no mapping found
    # For now, let's try to return something that might work, or let pandas fail
    # This simple replacement is a common case.
    if 'm' in timeframe_str: return timeframe_str.replace('m', 'T') # 'T' or 'min' for minutes
    if 'h' in timeframe_str: return timeframe_str.replace('h', 'H')
    if 'd' in timeframe_str: return timeframe_str.replace('d', 'D')
    if 'w' in timeframe_str: return timeframe_str.replace('w', 'W')

    # Default assumption or error
    # raise ValueError(f"Cannot map timeframe '{timeframe_str}' to pandas frequency string.")
    return timeframe_str # Default to passing it as is, hoping pandas understands
