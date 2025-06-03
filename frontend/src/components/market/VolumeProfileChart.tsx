import React, { useState, useEffect, useCallback } from 'react';
import DatePicker from 'react-datepicker'; // Assuming react-datepicker is installed
import "react-datepicker/dist/react-datepicker.css"; // Styles for DatePicker
import {
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    CartesianGrid,
    Cell,
    ReferenceLine, // For marking POC, VA High/Low lines
} from 'recharts'; // Assuming recharts is installed

import {
    fetchVolumeProfile,
    VolumeProfileData,
    FetchVolumeProfileParams,
    VolumeProfileLevelData,
} from '../../services/marketDataService';
import './VolumeProfileChart.css'; // To be created

interface VolumeProfileChartProps {
    exchange: string;
    symbol: string;
    globalTimeframe?: string; // Added global timeframe prop
}

const PROFILE_TYPE_OPTIONS: FetchVolumeProfileParams['profile_type'][] = ['daily', 'weekly', 'monthly', 'range'];

// Helper to parse timeframe string like "1m", "5m", "1h", "4h" to milliseconds
// This is a simplified parser. A library like 'ms' or 'parse-duration' would be more robust.
const parseSimpleTimeframeToMs = (tf: string): number => {
    const unit = tf.slice(-1);
    const value = parseInt(tf.slice(0, -1), 10);
    if (isNaN(value)) return 24 * 60 * 60 * 1000; // Default to 1 day if parse fails

    switch (unit) {
        case 'm': return value * 60 * 1000;
        case 'h': return value * 60 * 60 * 1000;
        case 'd': return value * 24 * 60 * 60 * 1000;
        default: return value * 60 * 1000; // Default to minutes if unit unknown
    }
};

// Helper to format date to YYYY-MM-DD string
const formatDateToYYYYMMDD = (date: Date): string => {
    return date.toISOString().split('T')[0];
};

const VolumeProfileChart: React.FC<VolumeProfileChartProps> = ({ exchange, symbol, globalTimeframe }) => {
    const [volumeProfileData, setVolumeProfileData] = useState<VolumeProfileData | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const [fetchParams, setFetchParams] = useState<FetchVolumeProfileParams>({
        profile_type: 'daily', // Default profile type
        date_utc: formatDateToYYYYMMDD(new Date()),
        // tick_size might be another prop or user input later
    });

    // Initialize range dates based on globalTimeframe if profile_type is 'range' initially or switched to.
    // For 'daily', 'weekly', 'monthly', date_utc is primary.
    const [rangeStartDate, setRangeStartDate] = useState<Date>(() => {
        const now = new Date();
        // If globalTimeframe is available and profile is 'range', try to set a meaningful default range.
        // This is a rough interpretation: set start date to be 'N bars of globalTimeframe ago'.
        // E.g., if globalTimeframe is '1h', set start to 24 hours ago (24 bars).
        // This specific logic might need refinement based on desired UX.
        // For now, let's use a fixed default like "last 24 hours" or "start of day".
        const d = new Date(now);
        d.setDate(d.getDate() - 1); // Default to last 24 hours for range initially
        d.setHours(0,0,0,0); // Start of that day
        return d;
    });
    const [rangeEndDate, setRangeEndDate] = useState<Date>(() => new Date()); // Default to now for range end


    const handleFetchData = useCallback(() => {
        setIsLoading(true);
        setError(null);

        let paramsToFetch: FetchVolumeProfileParams = { ...fetchParams };

        if (fetchParams.profile_type === 'range') {
            paramsToFetch.start_time_utc = rangeStartDate.toISOString();
            paramsToFetch.end_time_utc = rangeEndDate.toISOString();
            delete paramsToFetch.date_utc; // Not needed for range
        } else {
            // Ensure date_utc is set for period types, default to today if somehow null
            paramsToFetch.date_utc = fetchParams.date_utc || formatDateToYYYYMMDD(new Date());
            delete paramsToFetch.start_time_utc;
            delete paramsToFetch.end_time_utc;
        }

        fetchVolumeProfile(exchange, symbol, paramsToFetch)
            .then(data => {
                // Sort levels by price for correct rendering in vertical bar chart
                if (data.levels) {
                    data.levels.sort((a, b) => a.price - b.price);
                }
                setVolumeProfileData(data);
            })
            .catch(err => {
                if (err instanceof Error) setError(err.message);
                else setError("Failed to fetch volume profile data.");
            })
            .finally(() => setIsLoading(false));
    }, [exchange, symbol, fetchParams, rangeStartDate, rangeEndDate]);

    useEffect(() => {
        handleFetchData();
    }, [handleFetchData]);

    // Effect to potentially adjust date range or profile type when globalTimeframe changes
    useEffect(() => {
        if (globalTimeframe) {
            // If profile type is 'range', adjust the date range to reflect globalTimeframe view
            // Or, if a specific profile_type like "tf_based_session" is desired, switch to it.
            // For now, if 'range' is active, let's adjust the range to be e.g., last 100 bars of globalTimeframe.
            if (fetchParams.profile_type === 'range') {
                const now = new Date();
                const tfMs = parseSimpleTimeframeToMs(globalTimeframe);
                const calculatedStartDate = new Date(now.getTime() - (100 * tfMs)); // Example: last 100 bars

                // Only update if significantly different or as per specific logic
                // This is to avoid rapid updates if globalTimeframe changes frequently.
                // For this example, we'll just set it.
                setRangeStartDate(calculatedStartDate);
                setRangeEndDate(now);
                // Note: This will trigger a refetch via handleFetchData's dependencies if rangeStartDate/EndDate are included.
            }
            // If other profile types are selected, globalTimeframe might not directly apply,
            // unless we add logic to switch profile_type, e.g., to 'daily' if globalTimeframe is '1d'.
        }
    }, [globalTimeframe, fetchParams.profile_type]);


    const handleParamChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
        const { name, value } = e.target;
        setFetchParams(prev => ({ ...prev, [name]: value }));
    };

    const handleDateChange = (date: Date) => { // For 'daily', 'weekly', 'monthly'
        setFetchParams(prev => ({ ...prev, date_utc: formatDateToYYYYMMDD(date) }));
    };


    // Calculate domain for Y-axis (price) for better visualization
    const priceDomain: [number, number] | undefined = useMemo(() => {
        if (!volumeProfileData?.levels || volumeProfileData.levels.length === 0) return undefined;
        const prices = volumeProfileData.levels.map(l => l.price);
        const min = Math.min(...prices);
        const max = Math.max(...prices);
        const padding = (max - min) * 0.05; // 5% padding
        return [min - padding, max + padding];
    }, [volumeProfileData]);

    return (
        <div className="volume-profile-chart-container">
            <h4>Volume Profile: {symbol.toUpperCase()} on {exchange.toUpperCase()}</h4>
            <div className="vp-controls">
                <label>
                    Profile Type:
                    <select name="profile_type" value={fetchParams.profile_type} onChange={handleParamChange}>
                        {PROFILE_TYPE_OPTIONS.map(pt => <option key={pt} value={pt}>{pt.toUpperCase()}</option>)}
                    </select>
                </label>

                {fetchParams.profile_type !== 'range' && (
                    <label>
                        Date (UTC):
                        <DatePicker
                            selected={fetchParams.date_utc ? new Date(fetchParams.date_utc + "T00:00:00Z") : new Date()} // Ensure Date object
                            onChange={handleDateChange}
                            dateFormat="yyyy-MM-dd"
                        />
                    </label>
                )}

                {fetchParams.profile_type === 'range' && (
                    <>
                        <label>Start: <DatePicker selected={rangeStartDate} onChange={date => setRangeStartDate(date || new Date())} showTimeInput dateFormat="Pp" /></label>
                        <label>End: <DatePicker selected={rangeEndDate} onChange={date => setRangeEndDate(date || new Date())} showTimeInput dateFormat="Pp" /></label>
                    </>
                )}
                <label>
                    Tick Size (Opt.):
                    <input type="number" name="tick_size" value={fetchParams.tick_size || ''} onChange={handleParamChange} placeholder="e.g., 0.01" step="0.00001" min="0"/>
                </label>
                <button onClick={handleFetchData} disabled={isLoading}>
                    {isLoading ? "Loading..." : "Refresh"}
                </button>
            </div>

            {isLoading && <p>Loading volume profile...</p>}
            {error && <p className="error-message">Error: {error}</p>}

            {volumeProfileData && volumeProfileData.levels.length > 0 && (
                <div style={{ width: '100%', height: '400px' }}> {/* Adjust height */}
                    <ResponsiveContainer>
                        <BarChart layout="vertical" data={volumeProfileData.levels} margin={{ top: 5, right: 50, left: 10, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" dataKey="total_volume" name="Volume" tickFormatter={(vol) => (vol / 1000).toFixed(1) + 'k'} />
                            <YAxis
                                type="category"
                                dataKey="price"
                                name="Price"
                                width={70}
                                tickFormatter={(price) => Number(price).toFixed(2)} // Adjust precision as needed
                                domain={priceDomain}
                                reversed={false} // Prices typically low to high from bottom to top
                            />
                            <Tooltip
                                formatter={(value: number, name: string, props: any) => [`Vol: ${value.toFixed(2)}`, `Price: ${props.payload.price.toFixed(2)}`]}
                                labelFormatter={(label) => `Price: ${Number(label).toFixed(2)}`} // Label here is price
                            />
                            <Bar dataKey="total_volume" name="Volume at Price">
                                {volumeProfileData.levels.map((entry, index) => {
                                    let fillColor = "#8884d8"; // Default bar color
                                    const isPOC = volumeProfileData.point_of_control_price === entry.price;
                                    const isInVA = volumeProfileData.value_area_low && volumeProfileData.value_area_high &&
                                                   entry.price >= volumeProfileData.value_area_low && entry.price <= volumeProfileData.value_area_high;

                                    if (isPOC) {
                                        fillColor = "#ffc658"; // POC color (e.g., gold/yellow)
                                    } else if (isInVA) {
                                        fillColor = "#82ca9d"; // Value Area color (e.g., green)
                                    } else {
                                        fillColor = "#cccccc"; // Outside VA color (e.g., grey)
                                    }
                                    return <Cell key={`cell-${index}`} fill={fillColor} />;
                                })}
                            </Bar>
                            {/* Reference lines for POC, VA High, VA Low */}
                            {volumeProfileData.point_of_control_price && (
                                <ReferenceLine y={volumeProfileData.point_of_control_price} stroke="orange" strokeDasharray="3 3" strokeWidth={2}>
                                     <YAxis tickFormatter={() => `POC: ${volumeProfileData.point_of_control_price?.toFixed(2)}`} />
                                </ReferenceLine>
                            )}
                            {volumeProfileData.value_area_high && (
                                <ReferenceLine y={volumeProfileData.value_area_high} stroke="lightgreen" strokeDasharray="2 2">
                                     <YAxis tickFormatter={() => `VAH: ${volumeProfileData.value_area_high?.toFixed(2)}`} />
                                </ReferenceLine>
                            )}
                            {volumeProfileData.value_area_low && (
                                <ReferenceLine y={volumeProfileData.value_area_low} stroke="lightcoral" strokeDasharray="2 2">
                                    <YAxis tickFormatter={() => `VAL: ${volumeProfileData.value_area_low?.toFixed(2)}`} />
                                </ReferenceLine>
                            )}
                        </BarChart>
                    </ResponsiveContainer>
                     <div className="vp-summary">
                        {volumeProfileData.point_of_control_price && <p>POC: {volumeProfileData.point_of_control_price.toFixed(2)} (Vol: {volumeProfileData.point_of_control_volume?.toFixed(2)})</p>}
                        {volumeProfileData.value_area_low && volumeProfileData.value_area_high && <p>Value Area: {volumeProfileData.value_area_low.toFixed(2)} - {volumeProfileData.value_area_high.toFixed(2)}</p>}
                        <p>Total Profile Volume: {volumeProfileData.total_profile_volume.toFixed(2)}</p>
                    </div>
                </div>
            )}
            {!isLoading && volumeProfileData && volumeProfileData.levels.length === 0 && (
                <p>No volume profile data available for the selected criteria.</p>
            )}
        </div>
    );
};

export default VolumeProfileChart;
