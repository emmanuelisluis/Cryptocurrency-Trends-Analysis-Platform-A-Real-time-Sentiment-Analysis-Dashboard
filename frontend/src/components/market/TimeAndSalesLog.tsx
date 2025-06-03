import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { fetchRecentTrades, Trade, FetchTradesParams } from '../../services/marketDataService';
import './TimeAndSalesLog.css'; // We will create this CSS file next

interface TimeAndSalesLogProps {
    exchange: string;
    symbol: string;
    pollInterval?: number; // Milliseconds
}

const DEFAULT_LIMIT = 50; // Default number of trades to fetch

const TimeAndSalesLog: React.FC<TimeAndSalesLogProps> = ({
    exchange,
    symbol,
    pollInterval = 5000, // Default to 5 seconds
}) => {
    const [trades, setTrades] = useState<Trade[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [filterParams, setFilterParams] = useState<FetchTradesParams>({
        limit: DEFAULT_LIMIT,
        min_volume: 0, // Default to no min volume filter initially
    });
    // const [lastFetchTimestamp, setLastFetchTimestamp] = useState<string | undefined>(undefined); // Not used in simple "fetch latest N"
    const [largeTradeThreshold, setLargeTradeThreshold] = useState<number>(10); // Default threshold

    const fetchData = useCallback(async (currentFilters: FetchTradesParams, isPoll: boolean = false) => {
        setIsLoading(true);
        try {
            // For polling, we want to get trades *since* the last trade we received to avoid gaps
            // and reduce redundant data, but only if we have existing trades.
            // However, the subtask specified "fetch latest N" for simplicity in polling.
            // If we were to use `since_timestamp_utc` for polling:
            // const paramsToUse = isPoll && trades.length > 0 && lastFetchTimestamp
            // ? { ...currentFilters, since_timestamp_utc: lastFetchTimestamp, limit: undefined } // Get all since last, don't limit by number initially
            // : { ...currentFilters, since_timestamp_utc: undefined }; // Initial fetch or filter change

            const paramsToUse = { ...currentFilters, since_timestamp_utc: undefined }; // Simple "fetch latest N"

            const newTrades = await fetchRecentTrades(exchange, symbol, paramsToUse);

            setTrades(prevTrades => {
                // Simple replacement for "fetch latest N"
                return newTrades.sort((a,b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()); // Ensure descending sort
            });

            if (newTrades.length > 0) {
                 // Update timestamp for next potential `since_timestamp_utc` fetch if we were using that strategy
                // setLastFetchTimestamp(newTrades[0].timestamp); // Assuming trades are sorted newest first
            }
            setError(null);
        } catch (err) {
            if (err instanceof Error) setError(err.message);
            else setError('An unknown error occurred while fetching trades.');
        } finally {
            setIsLoading(false);
        }
    }, [exchange, symbol]); // Removed `trades` and `lastFetchTimestamp` from deps for "fetch latest N"

    useEffect(() => {
        fetchData(filterParams); // Initial fetch when component mounts or filters change

        const intervalId = setInterval(() => fetchData(filterParams, true), pollInterval);

        return () => {
            clearInterval(intervalId);
        };
    }, [exchange, symbol, filterParams, pollInterval, fetchData]);

    const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFilterParams(prevParams => ({
            ...prevParams,
            [name]: name === 'limit' || name === 'min_volume' ? parseFloat(value) || 0 : value,
        }));
    };

    // Memoize the displayed trades to prevent re-renders if trades array reference changes but content is same
    const displayedTrades = useMemo(() => trades.slice(0, filterParams.limit || DEFAULT_LIMIT), [trades, filterParams.limit]);

    return (
        <div className="time-and-sales">
            <h4>Time & Sales: {symbol.toUpperCase()} on {exchange.toUpperCase()}</h4>

            <div className="filters-bar">
                <label>
                    Limit:
                    <input
                        type="number"
                        name="limit"
                        value={filterParams.limit || DEFAULT_LIMIT}
                        onChange={handleFilterChange}
                        min="1"
                        max="500" // Consistent with backend Pydantic model if desired
                    />
                </label>
                <label>
                    Min Volume:
                    <input
                        type="number"
                        name="min_volume"
                        value={filterParams.min_volume || 0}
                        onChange={handleFilterChange}
                        step="0.0001"
                        min="0"
                    />
                </label>
                <label>
                    Large Vol Min:
                    <input
                        type="number"
                        name="largeTradeThreshold"
                        value={largeTradeThreshold}
                        onChange={(e) => setLargeTradeThreshold(parseFloat(e.target.value) || 0)}
                        step="0.1" // Or appropriate step for typical volumes
                        min="0"
                    />
                </label>
            </div>

            {isLoading && trades.length === 0 && <p>Loading trades...</p>}
            {isLoading && trades.length > 0 && <p style={{fontSize: '0.8em', fontStyle: 'italic', textAlign: 'center'}}>Refreshing trades...</p>}
            {error && <p className="error-message">Error: {error}</p>}

            <div className="trades-log-container">
                <div className="trades-log-header">
                    <span>Time</span>
                    <span>Price</span>
                    <span>Volume</span>
                    <span>Side</span>
                </div>
                <div className="trades-log">
                    {displayedTrades.map(trade => {
                        let tradeClasses = `trade-entry ${trade.side.toLowerCase()}`;
                        if (largeTradeThreshold > 0 && trade.volume >= largeTradeThreshold) {
                            tradeClasses += ' large-trade';
                        }
                        return (
                            <div key={trade.trade_id} className={tradeClasses}>
                                <span>{new Date(trade.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 })}</span>
                                <span>{trade.price.toFixed(2)}</span> {/* Adjust toFixed based on symbol's precision */}
                                <span>{trade.volume.toFixed(4)}</span> {/* Adjust toFixed based on symbol's precision */}
                                <span className="side">{trade.side.toUpperCase()}</span>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default TimeAndSalesLog;
