import React, { useState, useEffect, useMemo } from 'react';
import {
    ResponsiveContainer,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    Tooltip,
    CartesianGrid,
    Legend,
} from 'recharts';
import {
    fetchOrderBookSnapshot,
    OrderBookSnapshot,
    ImbalanceAtDepth,
    OBDGData
} from '../../services/marketDataService';
import './OrderBookDepthChart.css'; // Assuming styles are in this file

/**
 * Props for the OrderBookDepthChart component.
 */
interface OrderBookDepthChartProps {
    /** The exchange from which to fetch data. */
    exchange: string;
    /** The trading symbol (e.g., "btcusdt"). */
    symbol: string;
    /** Interval in milliseconds for polling data. Defaults to 5000ms. */
    pollInterval?: number;
}

/**
 * Processes raw order book snapshot data to prepare it for depth chart rendering.
 * Calculates cumulative quantities for bids and asks.
 * @param data The raw OrderBookSnapshot data from the API.
 * @param maxLevels Maximum number of bid/ask levels to process and display.
 * @returns An object containing processed bid and ask data arrays suitable for Recharts.
 */
const processOrderBookForChart = (data: OrderBookSnapshot | null, maxLevels: number = 20) => {
    if (!data) {
        return { bids: [], asks: [] };
    }

    let cumulativeBidQuantity = 0;
    // Process bids: sort by price descending, take top N, calculate cumulative quantity
    const processedBids = data.bids
        .slice(0, maxLevels)
        .sort((a, b) => b.price - a.price)
        .map(level => {
            cumulativeBidQuantity += level.quantity;
            return {
                price: level.price,
                quantity: level.quantity,
                cumulativeQuantity: cumulativeBidQuantity,
            };
        });

    let cumulativeAskQuantity = 0;
    const processedAsks = data.asks
        .slice(0, maxLevels)
        .sort((a, b) => a.price - b.price)
        .map(level => {
            cumulativeAskQuantity += level.quantity;
            return {
                price: level.price,
                quantity: level.quantity,
                cumulativeQuantity: cumulativeAskQuantity,
            };
        });
    // Process asks: sort by price ascending, take top N, calculate cumulative quantity
    const processedAsks = data.asks
        .slice(0, maxLevels)
        .sort((a, b) => a.price - b.price)
        .map(level => {
            cumulativeAskQuantity += level.quantity;
            return {
                price: level.price,
                quantity: level.quantity,
                cumulativeQuantity: cumulativeAskQuantity,
            };
        });
    return { bids: processedBids, asks: processedAsks };
};

/**
 * Sub-component to display Order Book Imbalance statistics.
 * @param props Component props.
 * @param props.imbalances Array of imbalance data.
 */
const OrderBookImbalanceDisplay: React.FC<{ imbalances: ImbalanceAtDepth[] }> = ({ imbalances }) => {
    // Note: Inline styles are used here for brevity in this example.
    // In a larger application, these would ideally be in a CSS file.
    return (
        <div className="order-book-imbalances">
            <h4>Order Book Imbalance</h4>
            {imbalances.map((imb) => (
                <div key={imb.depth_level} className="imbalance-level">
                    <p>
                        <strong>Depth {imb.depth_level}:</strong>
                        Bid Vol: {imb.bid_volume.toFixed(2)},
                        Ask Vol: {imb.ask_volume.toFixed(2)},
                        Ratio: {(imb.imbalance_ratio * 100).toFixed(1)}%
                    </p>
                    <div className="imbalance-bar-container">
                        <div
                            className="imbalance-bar-bid"
                            style={{ width: `${imb.imbalance_ratio * 100}%`}}
                            title={`Bid Side: ${(imb.imbalance_ratio * 100).toFixed(1)}%`}
                        />
                        <div
                            className="imbalance-bar-ask"
                            style={{ width: `${(1 - imb.imbalance_ratio) * 100}%`}}
                            title={`Ask Side: ${((1 - imb.imbalance_ratio) * 100).toFixed(1)}%`}
                        />
                    </div>
                </div>
            ))}
        </div>
    );
};

/**
 * Sub-component to display Order Book Depth Gradient (OBDG) statistics.
 * @param props Component props.
 * @param props.obdgData OBDG data object.
 */
const OBDGDisplay: React.FC<{ obdgData: OBDGData }> = ({ obdgData }) => {
    const formatRatio = (ratio?: number | null): string =>
        (ratio !== null && ratio !== undefined ? ratio.toFixed(2) : 'N/A');

    return (
        <div className="order-book-obdg-stats">
            <h5>
                Order Book Depth Gradient <br />
                (Near: {obdgData.near_market_depth} vs Far: {obdgData.far_market_depth_start}-{obdgData.far_market_depth_end})
            </h5>
            <p>Bid Ratio (Near/Far): <strong>{formatRatio(obdgData.bid_ratio_near_to_far)}</strong></p>
            <p>Ask Ratio (Near/Far): <strong>{formatRatio(obdgData.ask_ratio_near_to_far)}</strong></p>
            <p>Overall Gradient (Near/Far): <strong>{formatRatio(obdgData.overall_gradient_strength)}</strong></p>
        </div>
    );
};

/**
 * OrderBookDepthChart Component:
 * Fetches and displays order book depth data as an area chart,
 * along with imbalance and OBDG statistics.
 * Polls for new data at a specified interval.
 * @param props Component props.
 */
const OrderBookDepthChart: React.FC<OrderBookDepthChartProps> = ({
    exchange,
    symbol,
    pollInterval = 5000, // Default poll interval 5 seconds
}) => {
    const [orderBookData, setOrderBookData] = useState<OrderBookSnapshot | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    // Data fetching and polling effect
    useEffect(() => {
        let isMounted = true; // Flag to prevent state updates on unmounted component

        const fetchData = async () => {
            if (!isMounted) return;

            // Set loading state: true if no data yet, otherwise indicate refresh (isLoading remains false)
            if (!orderBookData) {
                setIsLoading(true);
            }
            // For subsequent fetches, isLoading might be set to a different "isRefreshing" state
            // or handled by observing if orderBookData timestamp changes.

            try {
                const data = await fetchOrderBookSnapshot(exchange, symbol);
                if (isMounted) {
                    setOrderBookData(data);
                    setError(null); // Clear any previous errors
                }
            } catch (err) {
                if (isMounted) {
                    if (err instanceof Error) {
                        setError(err.message);
                    } else {
                        setError('An unknown error occurred while fetching order book data.');
                    }
                    // Optionally, keep stale data by not setting orderBookData to null,
                    // or clear it: setOrderBookData(null);
                }
            } finally {
                if (isMounted) {
                    setIsLoading(false); // Set loading to false after fetch attempt
                }
            }
        };

        fetchData(); // Initial fetch
        const intervalId = setInterval(fetchData, pollInterval); // Setup polling

        // Cleanup function for when the component unmounts or dependencies change
        return () => {
            isMounted = false;
            clearInterval(intervalId);
        };
    }, [exchange, symbol, pollInterval]); // Removed orderBookData from deps: Polling should not depend on data changing.
                                          // Re-fetching is based on interval.

    // Memoized processed chart data
    const chartData = useMemo(() => processOrderBookForChart(orderBookData), [orderBookData]);

    // Conditional rendering based on state
    if (isLoading && !orderBookData) {
        return <div className="chart-loading-message">Loading depth chart for {symbol.toUpperCase()} on {exchange.toUpperCase()}...</div>;
    }

    if (error) {
        return <div className="chart-error-message">Error: {error} (while fetching {symbol.toUpperCase()} on {exchange.toUpperCase()})</div>;
    }

    if (!orderBookData || (chartData.bids.length === 0 && chartData.asks.length === 0)) { // Check both bids and asks
        return <div className="chart-no-data-message">No order book data available for {symbol.toUpperCase()} on {exchange.toUpperCase()}.</div>;
    }

    // Determine price domain for Y-axis for better chart readability
    const allPrices = [...chartData.bids.map(b => b.price), ...chartData.asks.map(a => a.price)];
    const yPriceDomain: [number, number] = allPrices.length > 0
        ? [Math.min(...allPrices) * 0.995, Math.max(...allPrices) * 1.005]
        : ['auto', 'auto']; // Fallback if no prices (should be caught by no data message)


    return (
        <div className="order-book-depth-chart-wrapper">
            <h4> {/* Title moved to MarketViewPage for global context */}
                {/* Order Book Depth: {symbol.toUpperCase()} on {exchange.toUpperCase()} */}
            </h4>
            {isLoading && orderBookData && <p className="chart-refresh-indicator">Refreshing...</p>}

            <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                    <AreaChart data={chartData.bids.concat(chartData.asks)} /* Pass combined for domain calculation if needed, but individual data props on <Area> are key */
                               margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            type="number"
                            dataKey="cumulativeQuantity"
                            name="Cumulative Quantity"
                            tickFormatter={(val) => `${(val / 1000).toFixed(1)}k`} // Example: format large numbers
                            // reversed={false} // Consider if one side needs reversal for traditional depth chart look
                        />
                        <YAxis
                            type="number"
                            dataKey="price"
                            name="Price"
                            domain={yPriceDomain}
                            allowDataOverflow
                            tickFormatter={(price) => Number(price).toFixed(2)} // Ensure price is number before toFixed
                            orientation="right" // Common to have price on right for depth charts
                        />
                        <Tooltip
                            formatter={(value: number, name: string, props: any) => {
                                const pointData = props.payload;
                                return [`${pointData.quantity.toFixed(4)} @ ${pointData.price.toFixed(2)} (Cum: ${Number(value).toFixed(4)})`, name];
                            }}
                            labelFormatter={(label, payload) => {
                                // Label might be cumulative quantity if XAxis is quantity.
                                // If XAxis is price, label would be price.
                                // Try to get price from payload if available.
                                if (payload && payload.length > 0 && payload[0].payload.price) {
                                     return `Price: ${payload[0].payload.price.toFixed(2)}`;
                                }
                                return `Cum.Qty: ${Number(label).toFixed(2)}`;
                            }}
                        />
                        <Legend />
                        <Area
                            type="stepAfter"
                            dataKey="price" // Y-values for the area chart come from the 'price' field
                            name="Bids"
                            data={chartData.bids}
                            stroke="#00B167"
                            fill="#00B167"
                            fillOpacity={0.3}
                            connectNulls
                        />
                        <Area
                            type="stepAfter"
                            dataKey="price" // Y-values for the area chart come from the 'price' field
                            name="Asks"
                            data={chartData.asks}
                            stroke="#FF5733"
                            fill="#FF5733"
                            fillOpacity={0.3}
                            connectNulls
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
            <p className="chart-axes-note">
                X-axis: Cumulative Quantity, Y-axis: Price. (Bids from right-to-left, Asks from left-to-right if XAxis reversed for one)
            </p>

            {orderBookData.imbalances && orderBookData.imbalances.length > 0 && (
                <OrderBookImbalanceDisplay imbalances={orderBookData.imbalances} />
            )}

            {orderBookData.obdg_data && (
                <OBDGDisplay obdgData={orderBookData.obdg_data} />
            )}
        </div>
    );
};

export default OrderBookDepthChart;
