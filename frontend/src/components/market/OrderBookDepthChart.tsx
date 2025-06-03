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
} from 'recharts'; // Assuming recharts is installed
import { fetchOrderBookSnapshot, OrderBookSnapshot, ImbalanceAtDepth } from '../../services/marketDataService'; // Added ImbalanceAtDepth

interface OrderBookDepthChartProps {
    exchange: string;
    symbol: string;
    pollInterval?: number; // Milliseconds
}

// Helper function to process order book data for charting
const processOrderBookForChart = (data: OrderBookSnapshot | null, maxLevels: number = 20) => {
    if (!data) return { bids: [], asks: [] };

    let cumulativeBidQuantity = 0;
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
    return { bids: processedBids, asks: processedAsks };
};

const OrderBookImbalanceDisplay: React.FC<{ imbalances: ImbalanceAtDepth[] }> = ({ imbalances }) => {
    if (!imbalances || imbalances.length === 0) {
        return <p>No imbalance data available.</p>;
    }
    return (
        <div className="order-book-imbalances" style={{ marginTop: '20px', padding: '10px', border: '1px solid #eee', borderRadius: '4px' }}>
            <h4>Order Book Imbalance:</h4>
            {imbalances.map((imb) => (
                <div key={imb.depth_level} className="imbalance-level" style={{ marginBottom: '10px', paddingBottom: '5px', borderBottom: '1px dashed #f0f0f0' }}>
                    <p style={{ margin: '2px 0', fontSize: '0.9em' }}>
                        <strong>Depth {imb.depth_level}:</strong>
                        Bid Vol: {imb.bid_volume.toFixed(2)},
                        Ask Vol: {imb.ask_volume.toFixed(2)},
                        Ratio: {(imb.imbalance_ratio * 100).toFixed(1)}%
                    </p>
                    <div style={{ display: 'flex', height: '18px', backgroundColor: '#ddd', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                            style={{
                                width: `${imb.imbalance_ratio * 100}%`,
                                backgroundColor: 'rgba(0, 177, 103, 0.7)', // Green for bids
                                height: '100%',
                                transition: 'width 0.3s ease-in-out',
                            }}
                            title={`Bid Side: ${(imb.imbalance_ratio * 100).toFixed(1)}%`}
                        />
                        <div
                            style={{
                                width: `${(1 - imb.imbalance_ratio) * 100}%`,
                                backgroundColor: 'rgba(255, 87, 51, 0.7)', // Red for asks
                                height: '100%',
                                transition: 'width 0.3s ease-in-out',
                            }}
                            title={`Ask Side: ${((1 - imb.imbalance_ratio) * 100).toFixed(1)}%`}
                        />
                    </div>
                </div>
            ))}
        </div>
    );
};


const OrderBookDepthChart: React.FC<OrderBookDepthChartProps> = ({
    exchange,
    symbol,
    pollInterval = 5000,
}) => {
    const [orderBookData, setOrderBookData] = useState<OrderBookSnapshot | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let isMounted = true;
        const fetchData = async () => {
            if (!isMounted) return;
            // Keep previous loading state if we already have data (for smoother refresh)
            if (!orderBookData) setIsLoading(true);
            else setIsLoading(false); // Or set a specific "isRefreshing" state

            try {
                const data = await fetchOrderBookSnapshot(exchange, symbol);
                if (isMounted) {
                    setOrderBookData(data);
                    setError(null);
                }
            } catch (err) {
                if (isMounted) {
                    if (err instanceof Error) setError(err.message);
                    else setError('An unknown error occurred.');
                }
            } finally {
                if (isMounted) setIsLoading(false);
            }
        };

        fetchData();
        const intervalId = setInterval(fetchData, pollInterval);
        return () => {
            isMounted = false;
            clearInterval(intervalId);
        };
    }, [exchange, symbol, pollInterval, orderBookData]); // Added orderBookData to dependencies to control setIsLoading correctly on refresh

    const chartData = useMemo(() => processOrderBookForChart(orderBookData), [orderBookData]);

    if (isLoading && !orderBookData) {
        return <div>Loading depth chart for {symbol} on {exchange}...</div>;
    }

    if (error) {
        return <div style={{ color: 'red' }}>Error: {error} (fetching {symbol} on {exchange})</div>;
    }

    if (!orderBookData || chartData.bids.length === 0 || chartData.asks.length === 0) {
        return <div>No order book data available for {symbol} on {exchange}.</div>;
    }

    const allPrices = [...chartData.bids.map(b => b.price), ...chartData.asks.map(a => a.price)];
    const yDomain = [Math.min(...allPrices) * 0.995, Math.max(...allPrices) * 1.005];

    return (
        <div style={{border: '1px solid #ccc', padding: '15px', borderRadius: '5px'}}>
            <h4 style={{ textAlign: 'center', marginBottom: '10px' }}>
                Order Book Depth: {symbol.toUpperCase()} on {exchange.toUpperCase()}
            </h4>
            {isLoading && <p style={{fontSize: '0.8em', textAlign: 'center', fontStyle: 'italic'}}>Refreshing...</p>}

            <div style={{ width: '100%', height: 300 }}> {/* Chart container */}
                <ResponsiveContainer>
                    <AreaChart margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            type="number"
                            dataKey="cumulativeQuantity"
                            name="Cumulative Quantity"
                            // reversed for bids might be an option depending on desired chart orientation
                        />
                        <YAxis
                            type="number"
                            dataKey="price"
                            name="Price"
                            domain={yDomain}
                            allowDataOverflow
                            tickFormatter={(price) => price.toFixed(2)} // Simplified formatting
                        />
                        <Tooltip
                            formatter={(value: number, name: string) => [value.toFixed(2), name]}
                            labelFormatter={(label) => `Cum. Qty: ${label.toFixed(2)}`}
                        />
                        <Legend />
                        <Area
                            type="stepAfter"
                            dataKey="price" // Y-value for the area
                            data={chartData.bids}
                            stroke="#00B167"
                            fill="#00B167"
                            fillOpacity={0.3}
                            name="Bids"
                            connectNulls
                        />
                        <Area
                            type="stepAfter"
                            dataKey="price" // Y-value for the area
                            data={chartData.asks}
                            stroke="#FF5733"
                            fill="#FF5733"
                            fillOpacity={0.3}
                            name="Asks"
                            connectNulls
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
            <p style={{fontSize: '0.8em', textAlign: 'center', color: '#555'}}>
                X-axis: Cumulative Quantity, Y-axis: Price.
            </p>

            {/* Display Imbalance Data */}
            {orderBookData.imbalances && (
                <OrderBookImbalanceDisplay imbalances={orderBookData.imbalances} />
            )}
        </div>
    );
};

export default OrderBookDepthChart;
