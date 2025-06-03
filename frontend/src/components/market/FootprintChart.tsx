import React, { useState, useEffect, useCallback, useMemo } from 'react';
import DatePicker from 'react-datepicker'; // Assuming react-datepicker is installed
import "react-datepicker/dist/react-datepicker.css";
import {
    ResponsiveContainer,
    BarChart, // Using BarChart as a base for custom shapes
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    CartesianGrid,
    Cell, // For coloring cells within a bar if using that approach
    Customized, // For more complex custom rendering
} from 'recharts'; // Assuming recharts is installed

import {
    fetchFootprintData,
    FootprintChartData,
    FootprintBarData,
    FootprintPriceLevelData,
    FetchFootprintParams,
} from '../../services/marketDataService';
import './FootprintChart.css'; // To be created

interface FootprintChartProps {
    exchange: string;
    symbol: string;
}

const TIMEFRAME_OPTIONS = ["1m", "5m", "15m", "1h", "4h", "1d"];

// Helper to get min/max price from all visible bars for Y-axis domain
const getPriceDomain = (bars: FootprintBarData[]): [number, number] => {
    if (!bars || bars.length === 0) return [0, 0];
    let minPrice = Infinity;
    let maxPrice = -Infinity;
    bars.forEach(bar => {
        if (bar.low < minPrice) minPrice = bar.low;
        if (bar.high > maxPrice) maxPrice = bar.high;
    });
    return [minPrice, maxPrice];
};

// Helper to find Point of Control (POC) price for a bar
const getPointOfControlPrice = (priceLevels: FootprintPriceLevelData[]): number | null => {
    if (!priceLevels || priceLevels.length === 0) return null;
    return priceLevels.reduce((poc, current) => (current.total_volume > poc.total_volume ? current : poc), priceLevels[0]).price;
};


// --- Custom Bar Component for Footprint Cells ---
interface CustomFootprintBarProps {
    x?: number;
    y?: number;
    width?: number;
    height?: number;
    barData: FootprintBarData;
    yScale: (price: number) => number; // Function to map price to y-coordinate
    priceRange: [number, number]; // minPrice, maxPrice of the bar (bar.low, bar.high)
    barHeight: number; // Total height allocated for this bar on the Y-axis (price scale)
}

const CustomFootprintBarCell: React.FC<CustomFootprintBarProps> = ({ x = 0, y = 0, width = 0, height = 0, barData, yScale, priceRange, barHeight }) => {
    if (!barData || !barData.price_levels) return null;

    const candleWidth = Math.max(width * 0.2, 5); // Candlestick body width (20% of bar width)
    const candleX = x + (width - candleWidth) / 2;

    const pocPrice = getPointOfControlPrice(barData.price_levels);

    return (
        <g>
            {/* Candle Wick (High-Low) */}
            <line x1={x + width / 2} y1={yScale(barData.high)} x2={x + width / 2} y2={yScale(barData.low)} stroke="#ccc" strokeWidth={1} />
            {/* Candle Body (Open-Close) */}
            <rect
                x={candleX}
                y={yScale(Math.max(barData.open, barData.close))}
                width={candleWidth}
                height={Math.abs(yScale(barData.open) - yScale(barData.close)) || 1} // min height 1px
                fill={barData.close >= barData.open ? 'green' : 'red'}
            />

            {/* Footprint Cells (Bid x Ask) */}
            {barData.price_levels.map((level, index) => {
                const cellHeight = Math.abs(yScale(level.price) - yScale(level.price - (yScale.domain()[1] > yScale.domain()[0] ? 0.01 : -0.01) )) || 1; // Approximate height for one price tick
                                                                                                                                                // This needs a proper tick size for the symbol
                const cellY = yScale(level.price) - cellHeight / 2; // Center cell text on price level

                // Determine cell background color based on delta or imbalance
                let cellFill = 'rgba(200, 200, 200, 0.1)'; // Default/neutral
                if (level.delta > 0) cellFill = `rgba(0, 255, 0, ${Math.min(0.1 + (level.delta / (barData.total_delta || 1)) * 0.5, 0.6)})`; // Greenish for positive delta
                if (level.delta < 0) cellFill = `rgba(255, 0, 0, ${Math.min(0.1 + (Math.abs(level.delta) / (barData.total_delta || 1)) * 0.5, 0.6)})`; // Reddish for negative delta

                if (level.price === pocPrice) cellFill = 'rgba(255, 255, 0, 0.4)'; // Yellowish for POC

                const textFontSize = Math.min(Math.max(cellHeight * 0.3, 6), 10); // Dynamic font size based on cell height

                return (
                    <g key={`cell-${level.price}-${index}`}>
                        <rect x={x} y={cellY - cellHeight/2} width={width} height={cellHeight} fill={cellFill} stroke="#eee" strokeWidth={0.5} />
                        <text
                            x={x + width / 2}
                            y={cellY + textFontSize / 3} // Adjust for vertical centering
                            textAnchor="middle"
                            fontSize={textFontSize}
                            fill="#333"
                        >
                            {`${level.bid_volume.toFixed(1)}x${level.ask_volume.toFixed(1)}`}
                        </text>
                    </g>
                );
            })}
             {/* Total Delta for the bar */}
            <text x={x + width / 2} y={yScale(barData.low) + 15} textAnchor="middle" fontSize="10" fill={barData.total_delta >= 0 ? 'green' : 'red'}>
                Δ: {barData.total_delta.toFixed(2)}
            </text>
        </g>
    );
};


const FootprintChart: React.FC<FootprintChartProps> = ({ exchange, symbol }) => {
    const [footprintData, setFootprintData] = useState<FootprintChartData | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedTimeframe, setSelectedTimeframe] = useState<string>("5m");

    // Default date range: last 24 hours
    const [endDate, setEndDate] = useState<Date>(new Date());
    const [startDate, setStartDate] = useState<Date>(() => {
        const d = new Date();
        d.setDate(d.getDate() - 1); // 1 day ago
        return d;
    });

    const handleFetchData = useCallback(() => {
        setIsLoading(true);
        setError(null);

        const params: FetchFootprintParams = {
            timeframe: selectedTimeframe,
            start_time_utc: startDate.toISOString(),
            end_time_utc: endDate.toISOString(),
        };

        fetchFootprintData(exchange, symbol, params)
            .then(data => {
                setFootprintData(data);
            })
            .catch(err => {
                if (err instanceof Error) setError(err.message);
                else setError("Failed to fetch footprint data.");
            })
            .finally(() => setIsLoading(false));
    }, [exchange, symbol, selectedTimeframe, startDate, endDate]);

    useEffect(() => {
        handleFetchData();
    }, [handleFetchData]); // Fetch on initial mount and when params change

    const yPriceDomain = useMemo(() => getPriceDomain(footprintData?.bars || []), [footprintData]);

    // Calculate tick size (this is a simplification, real tick size depends on symbol)
    // For rendering cell heights. This is highly approximate.
    const tickSize = useMemo(() => {
        if (!footprintData || footprintData.bars.length === 0) return 0.01;
        const prices = footprintData.bars.flatMap(bar => bar.price_levels.map(pl => pl.price));
        if (prices.length < 2) return 0.01;
        const uniqueSortedPrices = [...new Set(prices)].sort((a,b) => a - b);
        const minDiff = uniqueSortedPrices.slice(1).reduce((min, p, i) => {
            const diff = p - uniqueSortedPrices[i]; // uniqueSortedPrices[i] is previous element
            return Math.min(min, diff);
        }, Infinity);
        return minDiff === Infinity ? 0.01 : minDiff;
    }, [footprintData]);


    return (
        <div className="footprint-chart-container">
            <h3>Footprint Chart: {symbol.toUpperCase()} on {exchange.toUpperCase()}</h3>
            <div className="footprint-controls">
                <label>
                    Timeframe:
                    <select value={selectedTimeframe} onChange={e => setSelectedTimeframe(e.target.value)}>
                        {TIMEFRAME_OPTIONS.map(tf => <option key={tf} value={tf}>{tf}</option>)}
                    </select>
                </label>
                <div className="date-pickers">
                    <label>Start: <DatePicker selected={startDate} onChange={(date: Date) => setStartDate(date)} showTimeInput dateFormat="Pp" /></label>
                    <label>End: <DatePicker selected={endDate} onChange={(date: Date) => setEndDate(date)} showTimeInput dateFormat="Pp" /></label>
                </div>
                <button onClick={handleFetchData} disabled={isLoading}>
                    {isLoading ? "Refreshing..." : "Refresh Data"}
                </button>
            </div>

            {isLoading && !footprintData && <p>Loading footprint data...</p>}
            {error && <p className="error-message">Error: {error}</p>}

            {!isLoading && footprintData && footprintData.bars.length === 0 && <p>No data available for the selected criteria.</p>}

            {footprintData && footprintData.bars.length > 0 && (
                <div style={{ width: '100%', height: '600px' }}> {/* Adjust height as needed */}
                    <ResponsiveContainer>
                        <BarChart data={footprintData.bars} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis
                                dataKey="timestamp"
                                tickFormatter={(ts) => new Date(ts).toLocaleTimeString()}
                                name="Time"
                            />
                            <YAxis
                                type="number"
                                domain={yPriceDomain} // [minPrice, maxPrice]
                                allowDataOverflow={true}
                                scale="linear" // Price scale
                                name="Price"
                                tickFormatter={(price) => price.toFixed(Math.max(2, String(tickSize).split('.')[1]?.length || 2))} // Dynamic precision based on tickSize
                            />
                            <Tooltip
                                labelFormatter={(label) => new Date(label).toLocaleString()}
                                // Custom tooltip can be complex, showing OHLCTT + delta
                            />
                            <Bar dataKey="total_volume" name="Total Volume per Bar (hidden bar for structure)">
                                {footprintData.bars.map((bar, index) => (
                                    <Cell key={`cell-${index}`} fill="rgba(0,0,0,0)" /> // Invisible bars, just for structure for Customized
                                ))}
                                <Customized
                                   key="custom_footprint_bars" // Add key prop here
                                   // @ts-ignore Recharts types might not fully support Customized with all props from Bar
                                   children={(props: any) => { // props gives x, y, width, height of each bar
                                        const { x, y, width, height, index, data,yAxis } = props; // data is footprintData.bars array
                                        if (index === undefined || !data[index] || !yAxis) return null;

                                        const barData = data[index] as FootprintBarData;

                                        // Create a price to Y-coordinate scale function from the YAxis props
                                        const yScaleFunc = (price: number) => yAxis.scale(price);

                                        return (
                                            <CustomFootprintBarCell
                                                x={x}
                                                y={y} // y is top of the bar cell in Recharts BarChart context
                                                width={width}
                                                height={height} // height is total height of the bar cell
                                                barData={barData}
                                                yScale={yScaleFunc}
                                                priceRange={[barData.low, barData.high]} // actual low/high of this bar
                                                barHeight={height} // total height allocated to this bar cell
                                            />
                                        );
                                    }}
                                />
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
};

export default FootprintChart;
