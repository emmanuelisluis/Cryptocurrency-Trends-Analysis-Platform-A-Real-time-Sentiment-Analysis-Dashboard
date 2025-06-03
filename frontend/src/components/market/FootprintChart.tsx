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
    MomentumSustainabilityInputFeatures,
    MomentumSustainabilityOutput,
    predictMomentumSustainability,
    BreakoutViabilityInputFeatures,
    BreakoutViabilityOutput,
    predictBreakoutViability,
    AbsorptionEventInputFeatures, // Added for Absorption
    AbsorptionOutcomeOutput,
    predictAbsorptionOutcome,
} from '../../services/marketDataService';
import './FootprintChart.css';

interface FootprintChartProps {
    exchange: string;
    symbol: string;
    globalTimeframe?: string; // Added global timeframe prop
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
    yScale: (price: number) => number;
    priceRange: [number, number];
    barHeight: number;
    onBarClick: (barData: FootprintBarData, predictionType: 'momentum' | 'breakout') => void;
    onPriceLevelClick: (barData: FootprintBarData, priceLevelData: FootprintPriceLevelData) => void;
}

const CustomFootprintBarCell: React.FC<CustomFootprintBarProps> = ({ x = 0, y = 0, width = 0, height = 0, barData, yScale, priceRange, barHeight, onBarClick, onPriceLevelClick }) => {
    if (!barData || !barData.price_levels) return null;

    const candleWidth = Math.max(width * 0.15, 3);
    const candleX = x + (width - candleWidth) / 2;

    const maxVolumeAtPriceInBar = Math.max(...barData.price_levels.map(pl => pl.total_volume), 0);
    const pocPrice = barData.price_levels.find(pl => pl.total_volume === maxVolumeAtPriceInBar && pl.total_volume > 0)?.price;

    const SIGNIFICANT_IMBALANCE_RATIO = 3; // Moved from main component for direct use here
    const UNFINISHED_AUCTION_IMBALANCE_RATIO = 3;
    const UNFINISHED_AUCTION_MIN_AGGRESSOR_VOLUME = 0.1;
    const UNFINISHED_AUCTION_CLOSE_PROXIMITY_TICKS = 2;
    const APPROX_TICK_SIZE = useMemo(() => {
        if (barData.price_levels.length < 2) return 0.01;
        const prices = barData.price_levels.map(p => p.price).sort((a, b) => a - b);
        const diffs = prices.slice(1).map((p, i) => p - prices[i]).filter(d => d > 0);
        return diffs.length > 0 ? Math.min(...diffs) : 0.01;
    }, [barData.price_levels]);

    const handleBarGroupClick = () => {
        // Pass both prediction types up, FootprintChart can decide which to run
        onBarClick(barData, 'momentum');
        onBarClick(barData, 'breakout');
    };

    const handleCellClick = (priceLevelData: FootprintPriceLevelData, event: React.MouseEvent) => {
        event.stopPropagation(); // Prevent triggering bar group click
        onPriceLevelClick(barData, priceLevelData);
    };

    return (
        <g className="footprint-bar" onClick={handleBarGroupClick} style={{ cursor: 'pointer' }}>
            <rect x={x} y={yScale(barData.high)} width={width} height={Math.abs(yScale(barData.high) - yScale(barData.low))} fill="transparent" />
            <line className="candle-wick" x1={x + width / 2} y1={yScale(barData.high)} x2={x + width / 2} y2={yScale(barData.low)} />
            <rect
                className={`candle-body ${barData.close >= barData.open ? 'bullish' : 'bearish'}`}
                x={candleX}
                y={yScale(Math.max(barData.open, barData.close))}
                width={candleWidth}
                height={Math.abs(yScale(barData.open) - yScale(barData.close)) || 1}
            />

            {/* Footprint Cells (Bid x Ask) */}
            {barData.price_levels.map((pl, index) => {
                // This cellHeight calculation is approximate and needs a proper tickSize for the symbol.
                // For now, assuming a small fixed proportion of the bar height or a minimum value.
                // A more accurate way is (yScale(pl.price) - yScale(pl.price - tickSize)) but tickSize itself is complex.
                // Let's assume price levels are contiguous for height calculation for now or use a fixed height.
                const nextPrice = index + 1 < barData.price_levels.length ? barData.price_levels[index + 1].price : pl.price + (yScale.domain()[1] > yScale.domain()[0] ? 0.0001 : -0.0001) ; // crude next price for height
                const prevPrice = index - 1 >= 0 ? barData.price_levels[index-1].price : pl.price - (yScale.domain()[1] > yScale.domain()[0] ? 0.0001 : -0.0001);

                // Calculate cell boundaries based on surrounding prices or a fixed tick size
                // This is simplified. True footprint needs precise price step (tick size).
                const priceTickApproximation = Math.abs(nextPrice - prevPrice) / 2 || Math.abs(yScale.domain()[1]-yScale.domain()[0]) / 50 ; // fallback if only one level
                const cellTopY = yScale(pl.price + priceTickApproximation / 2);
                const cellBottomY = yScale(pl.price - priceTickApproximation / 2);
                const cellHeight = Math.abs(cellBottomY - cellTopY);

                const cellY = Math.min(cellTopY, cellBottomY);


                let cellClassName = "footprint-cell-rect ";
                const isPOC = pl.price === pocPrice && pl.total_volume > 0;
                if (isPOC) cellClassName += "poc ";

                const askImbalance = pl.ask_volume >= pl.bid_volume * SIGNIFICANT_IMBALANCE_RATIO && pl.bid_volume > 0.0000001; // Avoid div by zero or tiny vol imbalance
                const bidImbalance = pl.bid_volume >= pl.ask_volume * UNFINISHED_AUCTION_IMBALANCE_RATIO && pl.ask_volume > UNFINISHED_AUCTION_MIN_AGGRESSOR_VOLUME;


                if (askImbalance) cellClassName += "imbalance-ask ";
                else if (bidImbalance) cellClassName += "imbalance-bid ";

                // Unfinished Auction Logic
                if (barData.price_levels.length > 0) {
                    const lowestPriceLevel = barData.price_levels[0];
                    const highestPriceLevel = barData.price_levels[barData.price_levels.length - 1];

                    // Simplified close proximity check (using APPROX_TICK_SIZE)
                    const isCloseNearLow = Math.abs(barData.close - lowestPriceLevel.price) <= (APPROX_TICK_SIZE * UNFINISHED_AUCTION_CLOSE_PROXIMITY_TICKS);
                    const isCloseNearHigh = Math.abs(barData.close - highestPriceLevel.price) <= (APPROX_TICK_SIZE * UNFINISHED_AUCTION_CLOSE_PROXIMITY_TICKS);

                    if (pl.price === lowestPriceLevel.price) {
                        const hasStrongBidAtLow = lowestPriceLevel.bid_volume >= lowestPriceLevel.ask_volume * UNFINISHED_AUCTION_IMBALANCE_RATIO &&
                                                  lowestPriceLevel.bid_volume > UNFINISHED_AUCTION_MIN_AGGRESSOR_VOLUME;
                        if (isCloseNearLow && hasStrongBidAtLow) {
                            cellClassName += "unfinished-auction-low ";
                        }
                    }

                    if (pl.price === highestPriceLevel.price) {
                        const hasStrongAskAtHigh = highestPriceLevel.ask_volume >= highestPriceLevel.bid_volume * UNFINISHED_AUCTION_IMBALANCE_RATIO &&
                                                   highestPriceLevel.ask_volume > UNFINISHED_AUCTION_MIN_AGGRESSOR_VOLUME;
                        if (isCloseNearHigh && hasStrongAskAtHigh) {
                            cellClassName += "unfinished-auction-high ";
                        }
                    }
                }

                const textFontSize = Math.min(Math.max(cellHeight * 0.25, 5), 9);

                return (
                    <g
                        key={`cell-${pl.price}-${index}`}
                        className="footprint-price-level"
                        onClick={(e) => handleCellClick(pl, e)}
                        style={{ cursor: 'cell' }} // Indicate cells are clickable for absorption
                    >
                        <rect x={x} y={cellY} width={width} height={cellHeight} className={cellClassName.trim()} />
                        <text
                            className="footprint-cell-text"
                            x={x + width / 2}
                            y={cellY + cellHeight / 2} // Vertically center text
                            dominantBaseline="middle"
                            textAnchor="middle"
                            fontSize={textFontSize}
                        >
                            {`${pl.bid_volume.toFixed(1)} x ${pl.ask_volume.toFixed(1)}`}
                        </text>
                        <text
                            className={`footprint-price-delta ${pl.delta > 0 ? 'positive' : pl.delta < 0 ? 'negative' : 'neutral'}`}
                            x={x + width / 2}
                            y={cellY + cellHeight / 2 + textFontSize + 2} // Delta below Bid x Ask
                            dominantBaseline="middle"
                            textAnchor="middle"
                            fontSize={textFontSize * 0.8} // Smaller font for delta
                        >
                            ({pl.delta.toFixed(1)})
                        </text>
                    </g>
                );
            })}
             {/* Total Delta for the bar, positioned at the bottom */}
            <text
                className={`footprint-bar-delta-text ${barData.total_delta >= 0 ? 'positive' : 'negative'}`}
                x={x + width / 2}
                y={yScale(barData.low) + (yScale(barData.high) > yScale(barData.low) ? 15 : -5) } // Adjust y based on candle direction for visibility
                textAnchor="middle"
            >
                Δ: {barData.total_delta.toFixed(2)}
            </text>
        </g>
    );
};


const FootprintChart: React.FC<FootprintChartProps> = ({ exchange, symbol, globalTimeframe }) => {
    const [footprintData, setFootprintData] = useState<FootprintChartData | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    // Initialize local timeframe with globalTimeframe or default
    const [selectedTimeframe, setSelectedTimeframe] = useState<string>(globalTimeframe || "5m");

    const [endDate, setEndDate] = useState<Date>(new Date());
    const [startDate, setStartDate] = useState<Date>(() => {
        const d = new Date();
        d.setDate(d.getDate() - 1);
        return d;
    });

    // State for ML Predictions
    const [momentumPrediction, setMomentumPrediction] = useState<MomentumSustainabilityOutput | null>(null);
    const [isPredictingMomentum, setIsPredictingMomentum] = useState(false); // Specific loading state
    const [momentumPredictionError, setMomentumPredictionError] = useState<string | null>(null);

    const [breakoutPrediction, setBreakoutPrediction] = useState<BreakoutViabilityOutput | null>(null);
    const [isPredictingBreakout, setIsPredictingBreakout] = useState(false);
    const [breakoutPredictionError, setBreakoutPredictionError] = useState<string | null>(null);
    const [customBreakoutLevel, setCustomBreakoutLevel] = useState<number | null>(null);

    const [absorptionPrediction, setAbsorptionPrediction] = useState<AbsorptionOutcomeOutput | null>(null);
    const [isPredictingAbsorption, setIsPredictingAbsorption] = useState(false);
    const [absorptionPredictionError, setAbsorptionPredictionError] = useState<string | null>(null);


    const handleFetchData = useCallback(() => {
        setIsLoading(true);
        setError(null);
        setMomentumPrediction(null);
        setBreakoutPrediction(null);
        setAbsorptionPrediction(null);

        const params: FetchFootprintParams = {
            timeframe: selectedTimeframe, // Use local state for actual fetch
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

    const handleBarClickForPrediction = useCallback(async (barData: FootprintBarData, predictionType: 'momentum' | 'breakout') => {
        if (predictionType === 'momentum') {
            setIsPredictingMomentum(true);
            setMomentumPredictionError(null);
            setMomentumPrediction(null);
            const features: MomentumSustainabilityInputFeatures = {
                bar_timestamp: barData.timestamp,
                bar_delta: barData.total_delta,
                bar_volume: barData.total_volume,
                recent_cvd_slope: null, // V1 simplification
                market_volatility_atr: null, // V1 simplification
            };
            try {
                const prediction = await predictMomentumSustainability(features);
                setMomentumPrediction(prediction);
            } catch (err) {
                if (err instanceof Error) setMomentumPredictionError(err.message);
                else setMomentumPredictionError("Momentum prediction failed.");
            } finally {
                setIsPredictingMomentum(false);
            }
        } else if (predictionType === 'breakout') {
            setIsPredictingBreakout(true);
            setBreakoutPredictionError(null);
            setBreakoutPrediction(null);

            // For V1, breakout level is bar's close. A UI to set this would be better.
            const breakoutLevel = customBreakoutLevel !== null ? customBreakoutLevel : barData.close;
            if (customBreakoutLevel === null) {
                 console.log("Using bar close as breakout level. For specific level, enter in input.");
            }

            const features: BreakoutViabilityInputFeatures = {
                breakout_price_level: breakoutLevel,
                bar_timestamp_breakout_attempt: barData.timestamp,
                volume_at_breakout_bar: barData.total_volume,
                delta_at_breakout_bar: barData.total_delta,
                recent_volatility_atr: null, // V1 simplification, could get from advanced metrics if available
                distance_from_key_level: null, // V1 simplification
            };
            try {
                const prediction = await predictBreakoutViability(features);
                setBreakoutPrediction(prediction);
            } catch (err) {
                if (err instanceof Error) setBreakoutPredictionError(err.message);
                else setBreakoutPredictionError("Breakout prediction failed.");
            } finally {
                setIsPredictingBreakout(false);
            }
        }
    }, [customBreakoutLevel]);

    const handlePriceLevelClickForAbsorption = useCallback(async (barData: FootprintBarData, priceLevelData: FootprintPriceLevelData) => {
        setIsPredictingAbsorption(true);
        setAbsorptionPredictionError(null);
        setAbsorptionPrediction(null);

        const features: AbsorptionEventInputFeatures = {
            event_timestamp: barData.timestamp,
            absorption_price_level: priceLevelData.price,
            volume_at_absorption_level: priceLevelData.total_volume,
            delta_at_absorption_level: priceLevelData.delta,
            total_bar_volume: barData.total_volume,
            total_bar_delta: barData.total_delta,
            // V1 Simplifications - these would ideally be derived or user-input
            price_action_leading_up: null,
            order_book_pressure_bids: null,
            order_book_pressure_asks: null,
        };

        try {
            const prediction = await predictAbsorptionOutcome(features);
            setAbsorptionPrediction(prediction);
        } catch (err) {
            if (err instanceof Error) setAbsorptionPredictionError(err.message);
            else setAbsorptionPredictionError("Absorption outcome prediction failed.");
        } finally {
            setIsPredictingAbsorption(false);
        }
    }, []);


    useEffect(() => {
        handleFetchData();
    }, [handleFetchData]);

    // Effect to update local timeframe state when globalTimeframe prop changes
    useEffect(() => {
        if (globalTimeframe && globalTimeframe !== selectedTimeframe) {
            setSelectedTimeframe(globalTimeframe);
            // Data will be refetched by the main useEffect due to handleFetchData dependency change (as selectedTimeframe is in its deps)
        }
    }, [globalTimeframe, selectedTimeframe]); // Include selectedTimeframe to avoid potential stale closure issues in more complex scenarios

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
            {error && <p className="error-message">Error: {error} <button onClick={() => setError(null)}>Dismiss</button></p>}
            {!isLoading && footprintData && footprintData.bars.length === 0 && <p>No data available for the selected criteria.</p>}

            {/* Prediction Display Areas */}
            <div className="predictions-area">
                {isPredictingMomentum && <p className="prediction-status">Calculating Momentum Sustainability...</p>}
                {momentumPredictionError && <p className="error-message">Momentum Prediction Error: {momentumPredictionError} <button onClick={() => setMomentumPredictionError(null)}>Dismiss</button></p>}
                {momentumPrediction && (
                    <div className="prediction-display momentum-prediction-display">
                        <h5>Momentum Score (Bar: {new Date(momentumPrediction.timestamp_event).toLocaleTimeString()}):</h5>
                        <p><strong>Score: {momentumPrediction.sustainability_score.toFixed(1)} / 10</strong></p>
                        <p>Confidence: {(momentumPrediction.confidence !== null && momentumPrediction.confidence !== undefined) ? (momentumPrediction.confidence * 100).toFixed(1) + '%' : 'N/A'}</p>
                        <p><small>Model: {momentumPrediction.model_version || 'N/A'}</small></p>
                        <button onClick={() => setMomentumPrediction(null)}>Dismiss</button>
                    </div>
                )}

                {isPredictingBreakout && <p className="prediction-status">Calculating Breakout Viability...</p>}
                {breakoutPredictionError && <p className="error-message">Breakout Prediction Error: {breakoutPredictionError} <button onClick={() => setBreakoutPredictionError(null)}>Dismiss</button></p>}
                {breakoutPrediction && (
                    <div className="prediction-display breakout-prediction-display">
                        <h5>Breakout Viability (Bar: {new Date(breakoutPrediction.timestamp_event).toLocaleTimeString()}, Level: {breakoutPrediction.breakout_price_level.toFixed(2)}):</h5>
                        <p>P(True Breakout): <strong>{(breakoutPrediction.probability_true_breakout * 100).toFixed(1)}%</strong></p>
                        <p>P(False Breakout): {(breakoutPrediction.probability_false_breakout * 100).toFixed(1)}%</p>
                        <p><small>Model: {breakoutPrediction.model_version || 'N/A'}</small></p>
                        <button onClick={() => setBreakoutPrediction(null)}>Dismiss</button>
                    </div>
                )}

                {isPredictingAbsorption && <p className="prediction-status">Calculating Absorption Outcome...</p>}
                {absorptionPredictionError && <p className="error-message">Absorption Prediction Error: {absorptionPredictionError} <button onClick={() => setAbsorptionPredictionError(null)}>Dismiss</button></p>}
                {absorptionPrediction && (
                    <div className="prediction-display absorption-prediction-display">
                        <h5>Absorption Outcome (Bar: {new Date(absorptionPrediction.timestamp_event).toLocaleTimeString()}, Level: {absorptionPrediction.absorption_price_level.toFixed(2)}):</h5>
                        <p><strong>Predicted: {absorptionPrediction.predicted_outcome_label}</strong></p>
                        <p>P(Reversal): {(absorptionPrediction.probability_reversal * 100).toFixed(1)}%</p>
                        <p>P(Continuation): {(absorptionPrediction.probability_continuation * 100).toFixed(1)}%</p>
                        <p>P(Consolidation): {(absorptionPrediction.probability_consolidation * 100).toFixed(1)}%</p>
                        <p><small>Model: {absorptionPrediction.model_version || 'N/A'}</small></p>
                        <button onClick={() => setAbsorptionPrediction(null)}>Dismiss</button>
                    </div>
                )}
            </div>
            <div className="breakout-level-input"> {/* This might need a more generic name if used for more than just breakout level */}
                <label htmlFor="customBreakoutLevel">Custom Breakout Level for Prediction: </label>
                <input
                    type="number"
                    id="customBreakoutLevel"
                    value={customBreakoutLevel === null ? '' : customBreakoutLevel}
                    onChange={(e) => setCustomBreakoutLevel(e.target.value === '' ? null : parseFloat(e.target.value))}
                    placeholder="Enter price (e.g., bar close)"
                />
                 <small> (Click a bar to use its close, or enter level then click bar)</small>
            </div>


            {footprintData && footprintData.bars.length > 0 && (
                <div style={{ width: '100%', height: '600px', userSelect: 'none' }}>
                    <ResponsiveContainer>
                        <BarChart
                            data={footprintData.bars}
                            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                            // Add onClick here if we want to trigger prediction by clicking the general chart area
                            // For bar-specific clicks, it's handled by CustomFootprintBarCell
                        >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="timestamp" tickFormatter={(ts) => new Date(ts).toLocaleTimeString()} name="Time" />
                            <YAxis type="number" domain={yPriceDomain} allowDataOverflow={true} scale="linear" name="Price" tickFormatter={(price) => price.toFixed(Math.max(2, String(tickSize).split('.')[1]?.length || 2))} />
                            <Tooltip labelFormatter={(label) => new Date(label).toLocaleString()} />
                            <Bar dataKey="total_volume" name="Total Volume per Bar (hidden bar for structure)" >
                                {footprintData.bars.map((bar, index) => (
                                    <Cell key={`cell-bg-${index}`} fill="rgba(0,0,0,0)" />
                                ))}
                                <Customized
                                   key="custom_footprint_bars"
                                   children={(props: any) => {
                                        const { x, y, width, height, index, data, yAxis } = props;
                                        if (index === undefined || !data[index] || !yAxis) return null;
                                        const barData = data[index] as FootprintBarData;
                                        const yScaleFunc = (price: number) => yAxis.scale(price);
                                        return (
                                            <CustomFootprintBarCell
                                                x={x} y={y} width={width} height={height}
                                                barData={barData} yScale={yScaleFunc}
                                                priceRange={[barData.low, barData.high]} barHeight={height}
                                                // Pass the unified bar click handler from FootprintChart
                                                onBarClick={(clickedBarData, type) => handleBarClickForPrediction(clickedBarData, type)}
                                                onPriceLevelClick={handlePriceLevelClickForAbsorption}
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
