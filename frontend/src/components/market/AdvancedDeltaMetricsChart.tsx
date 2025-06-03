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
    ComposedChart, // Can use ComposedChart if mixing line and bar, e.g. for DMRV components
} from 'recharts';

import {
    fetchAdvancedDeltaMetrics,
    AdvancedDeltaMetricsData,
    FetchAdvancedDeltaMetricsParams,
    DVPRDataPoint,
    DMRVDataPoint,
} from '../../services/marketDataService';
import './AdvancedDeltaMetricsChart.css'; // To be created

interface AdvancedDeltaMetricsChartProps {
    exchange: string;
    symbol: string;
    globalTimeframe?: string; // Added global timeframe prop
}

const TIMEFRAME_OPTIONS = ["1m", "5m", "15m", "1h", "4h", "1d"];

const AdvancedDeltaMetricsChart: React.FC<AdvancedDeltaMetricsChartProps> = ({ exchange, symbol }) => {
    const [metricsData, setMetricsData] = useState<AdvancedDeltaMetricsData | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const [endDate, setEndDate] = useState<Date>(new Date());
    const [startDate, setStartDate] = useState<Date>(() => {
        const d = new Date();
        d.setDate(d.getDate() - 1);
        return d;
    });

    const initialTimeframe = globalTimeframe || "5m";
    const [fetchParams, setFetchParams] = useState<FetchAdvancedDeltaMetricsParams>({
        timeframe: initialTimeframe,
        atr_period: 14,
        dmrv_short_ma: 5,
        dmrv_long_ma: 10,
        // start_time_utc and end_time_utc will be set from startDate/endDate state in handleFetchData
    });

    const handleFetchData = useCallback(() => {
        setIsLoading(true);
        setError(null);

        if (fetchParams.dmrv_short_ma && fetchParams.dmrv_long_ma && fetchParams.dmrv_short_ma >= fetchParams.dmrv_long_ma) {
            setError("DMRV Short MA period must be less than Long MA period.");
            setIsLoading(false);
            return;
        }

        const paramsToFetch: FetchAdvancedDeltaMetricsParams = {
            ...fetchParams,
            start_time_utc: startDate.toISOString(),
            end_time_utc: endDate.toISOString(),
        };

        fetchAdvancedDeltaMetrics(exchange, symbol, paramsToFetch)
            .then(data => {
                const processedData = {
                    ...data,
                    dvpr_points: data.dvpr_points.map(p => ({ ...p, timestamp: new Date(p.timestamp).getTime() })),
                    dmrv_points: data.dmrv_points.map(p => ({ ...p, timestamp: new Date(p.timestamp).getTime() })),
                };
                setMetricsData(processedData);
            })
            .catch(err => {
                if (err instanceof Error) setError(err.message);
                else setError("Failed to fetch advanced delta metrics.");
            })
            .finally(() => setIsLoading(false));
    }, [exchange, symbol, fetchParams, startDate, endDate]);

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
        const numValue = (name === 'atr_period' || name === 'dmrv_short_ma' || name === 'dmrv_long_ma')
                       ? parseInt(value, 10)
                       : value;
        setFetchParams(prev => ({ ...prev, [name]: numValue }));
    };

    return (
        <div className="advanced-delta-metrics-chart-container">
            <h4>Advanced Delta Metrics: {symbol.toUpperCase()} ({fetchParams.timeframe})</h4>
            <div className="adv-delta-controls">
                <label>TF: <select name="timeframe" value={fetchParams.timeframe} onChange={handleParamChange}>{TIMEFRAME_OPTIONS.map(tf => <option key={tf} value={tf}>{tf}</option>)}</select></label>
                <div className="date-pickers">
                    <label>Start: <DatePicker selected={startDate} onChange={(date: Date) => setStartDate(date || new Date())} showTimeInput dateFormat="Pp" /></label>
                    <label>End: <DatePicker selected={endDate} onChange={(date: Date) => setEndDate(date || new Date())} showTimeInput dateFormat="Pp" /></label>
                </div>
                <label>ATR P: <input type="number" name="atr_period" value={fetchParams.atr_period || 14} onChange={handleParamChange} min="1" style={{width: "50px"}} /></label>
                <label>DMRV Short: <input type="number" name="dmrv_short_ma" value={fetchParams.dmrv_short_ma || 5} onChange={handleParamChange} min="1" style={{width: "50px"}} /></label>
                <label>DMRV Long: <input type="number" name="dmrv_long_ma" value={fetchParams.dmrv_long_ma || 10} onChange={handleParamChange} min="1" style={{width: "50px"}} /></label>
                <button onClick={handleFetchData} disabled={isLoading}>{isLoading ? "Loading..." : "Refresh"}</button>
            </div>

            {isLoading && <p>Loading metrics data...</p>}
            {error && <p className="error-message">Error: {error}</p>}

            {!isLoading && metricsData && metricsData.dvpr_points.length === 0 && metricsData.dmrv_points.length === 0 && <p>No data available for the selected criteria.</p>}

            {metricsData && (
                <>
                    <h5>Delta Volume Pressure Ratio (DVPR)</h5>
                    {metricsData.dvpr_points.length > 0 ? (
                        <div style={{ width: '100%', height: '200px' }}>
                            <ResponsiveContainer>
                                <LineChart data={metricsData.dvpr_points} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis type="number" scale="time" dataKey="timestamp" domain={['dataMin', 'dataMax']} tickFormatter={(unixTime) => new Date(unixTime).toLocaleTimeString()} name="Time" />
                                    <YAxis dataKey="dvpr_value" name="DVPR" domain={['auto', 'auto']} tickFormatter={(val) => val?.toFixed(2) ?? ''}/>
                                    <Tooltip labelFormatter={(label) => new Date(label).toLocaleString()} formatter={(value: number, name: string, props: any) => [`Value: ${value?.toFixed(3) ?? 'N/A'}`, `Delta: ${props.payload.bar_delta?.toFixed(2)} | Vol: ${props.payload.bar_volume?.toFixed(2)} | ATR: ${props.payload.bar_atr?.toFixed(3)}`]} />
                                    <Legend />
                                    <Line type="monotone" dataKey="dvpr_value" name="DVPR" stroke="#ff7300" dot={false} strokeWidth={2} connectNulls={true} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    ) : <p>No DVPR data for this period.</p>}

                    <h5 style={{marginTop: '20px'}}>Delta Moving Average (DMRV)</h5>
                    {metricsData.dmrv_points.length > 0 ? (
                        <div style={{ width: '100%', height: '200px' }}>
                            <ResponsiveContainer>
                                <ComposedChart data={metricsData.dmrv_points} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis type="number" scale="time" dataKey="timestamp" domain={['dataMin', 'dataMax']} tickFormatter={(unixTime) => new Date(unixTime).toLocaleTimeString()} name="Time" />
                                    <YAxis yAxisId="left" dataKey="dmrv_value" name="DMRV" domain={['auto', 'auto']} tickFormatter={(val) => val?.toFixed(2) ?? ''} />
                                    <YAxis yAxisId="right" dataKey="short_delta_ma" name="Delta MAs" orientation="right" domain={['auto', 'auto']} tickFormatter={(val) => val?.toFixed(2) ?? ''} stroke="#8884d8" />
                                    <Tooltip labelFormatter={(label) => new Date(label).toLocaleString()} />
                                    <Legend />
                                    <Line yAxisId="left" type="monotone" dataKey="dmrv_value" name="DMRV (Short-Long)" stroke="#82ca9d" dot={false} strokeWidth={2} connectNulls={true}/>
                                    <Line yAxisId="right" type="monotone" dataKey="short_delta_ma" name={`Delta MA(${fetchParams.dmrv_short_ma})`} stroke="#8884d8" dot={false} strokeWidth={1} strokeDasharray="5 5" connectNulls={true}/>
                                    <Line yAxisId="right" type="monotone" dataKey="long_delta_ma" name={`Delta MA(${fetchParams.dmrv_long_ma})`} stroke="#ffc658" dot={false} strokeWidth={1} strokeDasharray="5 5" connectNulls={true}/>
                                </ComposedChart>
                            </ResponsiveContainer>
                        </div>
                    ): <p>No DMRV data for this period.</p>}
                </>
            )}
        </div>
    );
};

export default AdvancedDeltaMetricsChart;
