import React, { useState, useEffect, useCallback, useMemo } from 'react';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    CartesianGrid,
    Legend,
    ReferenceDot, // For marking points, though not strictly for lines
    Customized, // For drawing custom SVG elements like lines
} from 'recharts';

import {
    fetchCVDData,
    CVDChartData,
    FetchCVDParams,
    CVDDataPoint,
} from '../../services/marketDataService';
import './CVDChart.css'; // To be created

interface CVDChartProps {
    exchange: string;
    symbol: string;
    globalTimeframe?: string; // Added global timeframe prop
}

// Interfaces for Divergence Drawing
interface Point {
    x: number; // Chart X-coordinate (timestamp as number)
    y: number; // Chart Y-coordinate (cvd_value)
    timestamp: number; // Original timestamp (for data reference)
    value: number;     // Original cvd_value (for data reference)
}

interface DivergenceLine {
    id: string; // Unique ID for the line
    startPoint: Point;
    endPoint: Point;
    type: 'bullish' | 'bearish' | 'custom'; // For styling, default to 'custom'
}


const TIMEFRAME_OPTIONS = ["1m", "5m", "15m", "1h", "4h", "1d"];
const RESET_CONDITION_OPTIONS: FetchCVDParams['reset_condition'][] = ['none', 'daily'];

// Helper to format date to YYYY-MM-DD string for date_utc param if needed,
// but API expects ISO strings for start/end.
const formatDateToISO = (date: Date): string => date.toISOString();


const CVDChart: React.FC<CVDChartProps> = ({ exchange, symbol }) => {
    const [cvdData, setCvdData] = useState<CVDChartData | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const [endDate, setEndDate] = useState<Date>(new Date());
    const [startDate, setStartDate] = useState<Date>(() => {
        const d = new Date();
        d.setDate(d.getDate() - 1);
        return d;
    });

    // Initialize local timeframe with globalTimeframe or default, then store in fetchParams
    const initialTimeframe = globalTimeframe || "5m";
    const [fetchParams, setFetchParams] = useState<FetchCVDParams>({
        timeframe: initialTimeframe,
        reset_condition: "none",
        // start_time_utc and end_time_utc are set from startDate/endDate state in handleFetchData
    });

    // State for divergence drawing
    const [divergenceLines, setDivergenceLines] = useState<DivergenceLine[]>([]);
    const [isDrawingDivergence, setIsDrawingDivergence] = useState(false);
    const [tempStartPoint, setTempStartPoint] = useState<Point | null>(null);
    // Ref to access chart state (scales, etc.) - might be needed for coord conversion
    const chartRef = React.useRef<any>(null); // For Recharts LineChart instance

    const handleFetchData = useCallback(() => {
        setIsLoading(true);
        setError(null);
        // Clear lines when data re-fetches for new range/params
        // setDivergenceLines([]);
        // setTempStartPoint(null);

        const paramsToFetch: FetchCVDParams = {
            ...fetchParams,
            start_time_utc: startDate.toISOString(), // Use current startDate state
            end_time_utc: endDate.toISOString(),   // Use current endDate state
        };

        fetchCVDData(exchange, symbol, paramsToFetch)
            .then(data => {
                // Process timestamps for Recharts (convert to number - Unix milliseconds)
                if (data.cvd_points) {
                    data.cvd_points = data.cvd_points.map(p => ({
                        ...p,
                        timestamp: new Date(p.timestamp).getTime(),
                    // Ensure cvd_value is a number, Pydantic should handle this from backend
                    // but API might return string if not strictly typed in controller
                        cvd_value: Number(p.cvd_value)
                    }));
                }
                setCvdData(data);
            })
            .catch(err => {
                if (err instanceof Error) setError(err.message);
                else setError("Failed to fetch CVD data.");
            })
            .finally(() => setIsLoading(false));
    }, [exchange, symbol, fetchParams, startDate, endDate]); // Add startDate, endDate as deps

    useEffect(() => {
        handleFetchData();
    }, [handleFetchData]);

    // Effect to update local timeframe in fetchParams when globalTimeframe prop changes
    useEffect(() => {
        if (globalTimeframe && globalTimeframe !== fetchParams.timeframe) {
            setFetchParams(prevParams => ({ ...prevParams, timeframe: globalTimeframe }));
        }
    }, [globalTimeframe, fetchParams.timeframe]);


    const handleParamChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
        const { name, value } = e.target;
        setFetchParams(prev => ({
            ...prev,
            [name]: value as FetchCVDParams['timeframe'] | FetchCVDParams['reset_condition']
        }));
    };

    const handleChartClick = (event: any) => {
        if (!isDrawingDivergence || !event || !event.activePayload || event.activePayload.length === 0) {
            return;
        }

        const chartPayload = event.activePayload[0].payload; // This is a CVDDataPoint
        const clickedPoint: Point = {
            x: chartPayload.timestamp, // timestamp is already number (Unix ms)
            y: chartPayload.cvd_value,
            timestamp: chartPayload.timestamp,
            value: chartPayload.cvd_value,
        };

        if (!tempStartPoint) {
            setTempStartPoint(clickedPoint);
            // Optionally provide user feedback: "Line start point selected. Click to select end point."
        } else {
            const newLine: DivergenceLine = {
                id: `line-${Date.now()}`, // Simple unique ID
                startPoint: tempStartPoint,
                endPoint: clickedPoint,
                type: 'custom', // Default type, can be changed later if UI allows type selection
            };
            setDivergenceLines(prevLines => [...prevLines, newLine]);
            setTempStartPoint(null); // Reset for the next line
        }
    };

    const processedCvdPoints = useMemo(() => {
        return cvdData?.cvd_points.map(p => ({ ...p })) || [];
    }, [cvdData]);

    const toggleDrawingMode = () => {
        setIsDrawingDivergence(!isDrawingDivergence);
        setTempStartPoint(null); // Reset temp point when toggling mode
    };

    const clearLastLine = () => setDivergenceLines(prev => prev.slice(0, -1));
    const clearAllLines = () => setDivergenceLines([]);


    return (
        <div className="cvd-chart-container">
            <h4>CVD: {symbol.toUpperCase()} on {exchange.toUpperCase()} ({fetchParams.timeframe}, Reset: {fetchParams.reset_condition})</h4>
            <div className="cvd-controls">
                {/* Timeframe, Reset, Date Pickers */}
                <label>TF: <select name="timeframe" value={fetchParams.timeframe} onChange={handleParamChange}>{TIMEFRAME_OPTIONS.map(tf => <option key={tf} value={tf}>{tf}</option>)}</select></label>
                <label>Reset: <select name="reset_condition" value={fetchParams.reset_condition} onChange={handleParamChange}>{RESET_CONDITION_OPTIONS.map(rc => <option key={rc} value={rc}>{rc || 'none'}</option>)}</select></label>
                <div className="date-pickers">
                    <label>Start: <DatePicker selected={startDate} onChange={(date: Date) => setStartDate(date || new Date())} showTimeInput dateFormat="Pp" /></label>
                    <label>End: <DatePicker selected={endDate} onChange={(date: Date) => setEndDate(date || new Date())} showTimeInput dateFormat="Pp" /></label>
                </div>
                <button onClick={handleFetchData} disabled={isLoading}>{isLoading ? "Loading..." : "Refresh"}</button>
            </div>
            <div className="divergence-controls">
                <button onClick={toggleDrawingMode} className={isDrawingDivergence ? 'active' : ''}>
                    {isDrawingDivergence ? "Cancel Drawing" : "Draw Divergence"}
                </button>
                {isDrawingDivergence && tempStartPoint && <span className="draw-status">Start point selected. Click chart for end point.</span>}
                <button onClick={clearLastLine} disabled={divergenceLines.length === 0}>Clear Last Line</button>
                <button onClick={clearAllLines} disabled={divergenceLines.length === 0}>Clear All Lines</button>
            </div>

            {isLoading && <p>Loading CVD data...</p>}
            {error && <p className="error-message">Error: {error}</p>}
            {!isLoading && cvdData && cvdData.cvd_points.length === 0 && <p>No CVD data available for the selected criteria.</p>}

            {cvdData && cvdData.cvd_points.length > 0 && (
                <div style={{ width: '100%', height: '300px', cursor: isDrawingDivergence ? 'crosshair' : 'default' }}>
                    <ResponsiveContainer>
                        <LineChart
                            data={processedCvdPoints}
                            onClick={handleChartClick}
                            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                            // ref={chartRef} // Assign ref if needed for coordinate calculations
                        >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" scale="time" dataKey="timestamp" domain={['dataMin', 'dataMax']} tickFormatter={(unixTime) => new Date(unixTime).toLocaleTimeString()} name="Time" />
                            <YAxis dataKey="cvd_value" name="CVD" domain={['auto', 'auto']} />
                            <Tooltip labelFormatter={(label) => new Date(label).toLocaleString()} formatter={(value: number) => [value.toFixed(2), "CVD"]} />
                            <Legend />
                            <Line type="monotone" dataKey="cvd_value" name={`CVD (${fetchParams.reset_condition} reset)`} stroke="#8884d8" dot={false} strokeWidth={2} />

                            {/* Render Divergence Lines - This is the tricky part with Recharts */}
                            {/* Using Customized component to draw SVG lines directly.
                                This requires access to X and Y axis scales to convert data points to SVG coordinates.
                                Recharts does not easily expose these scales to Customized children in a simple way for arbitrary lines.
                                A common workaround is to use another transparent Bar or Line component and use its 'shape' prop,
                                or to calculate coordinates manually if chart dimensions and domain are known.
                                For simplicity, this V1 might have to approximate or defer perfect line rendering if scales are not accessible.
                            */}
                            <Customized
                                key={`divergence-lines-${divergenceLines.length}`} // Force re-render when lines change
                                children={(propsFromCustomized: any) => {
                                    const { xAxis, yAxis, width, height, offset } = propsFromCustomized;
                                    if (!xAxis || !yAxis || !width || !height || !offset) return null; // Scales not ready

                                    // These scales convert data values (timestamp, cvd_value) to SVG coordinates
                                    const xScale = xAxis.scale;
                                    const yScale = yAxis.scale;

                                    return (
                                        <g className="custom-divergence-lines">
                                            {divergenceLines.map(line => (
                                                <line
                                                    key={line.id}
                                                    x1={xScale(line.startPoint.timestamp) + offset.left}
                                                    y1={yScale(line.startPoint.value) + offset.top}
                                                    x2={xScale(line.endPoint.timestamp) + offset.left}
                                                    y2={yScale(line.endPoint.value) + offset.top}
                                                    stroke={line.type === 'bullish' ? 'green' : line.type === 'bearish' ? 'red' : 'purple'}
                                                    strokeWidth={2}
                                                    strokeDasharray={line.type !== 'custom' ? "5 5" : undefined}
                                                />
                                            ))}
                                            {/* Draw temporary line while user is selecting end point */}
                                            {isDrawingDivergence && tempStartPoint && event?.chartX && event?.chartY && (
                                                <line
                                                    x1={xScale(tempStartPoint.timestamp) + offset.left}
                                                    y1={yScale(tempStartPoint.value) + offset.top}
                                                    x2={event.chartX} // Mouse X relative to chart container
                                                    y2={event.chartY} // Mouse Y relative to chart container
                                                    stroke="rgba(128,0,128,0.5)" // Light purple for temp line
                                                    strokeWidth={1}
                                                    strokeDasharray="3 3"
                                                />
                                            )}
                                        </g>
                                    );
                                }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
};

export default CVDChart;
