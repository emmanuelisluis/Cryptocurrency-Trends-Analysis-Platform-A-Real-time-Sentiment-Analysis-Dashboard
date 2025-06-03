// Define TypeScript interfaces for the API response based on Pydantic models

export interface OrderBookLevel {
    price: number;
    quantity: number; // Corresponds to OrderBookLevelAPI's 'quantity'
}

export interface ImbalanceAtDepth {
    depth_level: number;
    bid_volume: number;
    ask_volume: number;
    imbalance_ratio: number;
}

export interface OrderBookSnapshot {
    timestamp: string; // ISO 8601 datetime string
    symbol: string;
    exchange: string;
    bids: OrderBookLevel[];
    asks: OrderBookLevel[];
    last_update_id?: number;
    imbalances?: ImbalanceAtDepth[];
    obdg_data?: OBDGData;
}

// Interface for OBDG Data
export interface OBDGData {
    near_market_depth: number;
    far_market_depth_start: number;
    far_market_depth_end: number;
    bid_ratio_near_to_far?: number | null;
    ask_ratio_near_to_far?: number | null;
    overall_gradient_strength?: number | null;
}


// Interfaces for CVD (Cumulative Volume Delta) Data
export interface CVDDataPoint {
    timestamp: string;
    cvd_value: number;
}

export interface CVDChartData {
    exchange: string;
    symbol: string;
    timeframe: string;
    reset_condition: string;
    cvd_points: CVDDataPoint[];
}

export interface FetchCVDParams {
    timeframe: string;
    start_time_utc?: string;
    end_time_utc?: string;
    reset_condition?: 'none' | 'daily';
}


// Interfaces for Advanced Delta Metrics (DVPR, DMRV)
export interface DVPRDataPoint {
    timestamp: string; // or Date
    dvpr_value?: number | null;
    bar_delta: number;
    bar_volume: number;
    bar_atr?: number | null;
}

export interface DMRVDataPoint {
    timestamp: string; // or Date
    short_delta_ma?: number | null;
    long_delta_ma?: number | null;
    dmrv_value?: number | null;
}

export interface AdvancedDeltaMetricsData {
    exchange: string;
    symbol: string;
    timeframe: string;
    dvpr_points: DVPRDataPoint[];
    dmrv_points: DMRVDataPoint[];
}

export interface FetchAdvancedDeltaMetricsParams {
    timeframe: string;
    start_time_utc?: string; // ISO
    end_time_utc?: string; // ISO
    atr_period?: number;
    dmrv_short_ma?: number;
    dmrv_long_ma?: number;
}


// Interfaces for ML Predictions
export interface MomentumSustainabilityInputFeatures {
    bar_timestamp: string; // ISO datetime string
    bar_delta: number;
    bar_volume: number;
    recent_cvd_slope?: number | null;
    market_volatility_atr?: number | null;
    // Add other features if defined in backend Pydantic model
}

export interface MomentumSustainabilityOutput {
    timestamp_event: string; // ISO datetime string
    sustainability_score: number;
    confidence?: number | null;
    model_version?: string | null;
}

// Interfaces for Breakout Viability Prediction
export interface BreakoutViabilityInputFeatures {
    breakout_price_level: number;
    bar_timestamp_breakout_attempt: string; // ISO datetime string
    volume_at_breakout_bar: number;
    delta_at_breakout_bar: number;
    recent_volatility_atr?: number | null;
    distance_from_key_level?: number | null;
}

export interface BreakoutViabilityOutput {
    timestamp_event: string; // ISO datetime string
    breakout_price_level: number;
    probability_true_breakout: number;
    probability_false_breakout: number;
    model_version?: string | null;
}

// Interfaces for Absorption Event Outcome Prediction
export interface AbsorptionEventInputFeatures {
    event_timestamp: string; // ISO datetime string
    absorption_price_level: number;
    volume_at_absorption_level: number;
    delta_at_absorption_level: number;
    total_bar_volume: number;
    total_bar_delta: number;
    price_action_leading_up?: string | null;
    order_book_pressure_bids?: number | null;
    order_book_pressure_asks?: number | null;
}

export interface AbsorptionOutcomeOutput {
    timestamp_event: string; // ISO datetime string
    absorption_price_level: number;
    predicted_outcome_label: string; // "Reversal", "Continuation", "Consolidation"
    probability_reversal: number;
    probability_continuation: number;
    probability_consolidation: number;
    model_version?: string | null;
}


// Interfaces for Volume Profile Data
export interface VolumeProfileLevelData {
    price: number;
    total_volume: number;
}

export interface VolumeProfileData {
    profile_type: string;
    start_time_utc: string; // ISO 8601 datetime string
    end_time_utc: string;   // ISO 8601 datetime string
    levels: VolumeProfileLevelData[];
    point_of_control_price?: number;
    point_of_control_volume?: number;
    value_area_high?: number;
    value_area_low?: number;
    total_profile_volume: number;
}

export interface FetchVolumeProfileParams {
    profile_type: 'daily' | 'weekly' | 'monthly' | 'range';
    date_utc?: string;          // YYYY-MM-DD for daily/weekly/monthly
    start_time_utc?: string;    // ISO 8601 string for range
    end_time_utc?: string;      // ISO 8601 string for range
    tick_size?: number;
}



// Interfaces for Trade Data (as previously defined)
export interface Trade {
    timestamp: string;
    symbol: string;
    exchange: string;
    price: number;
    volume: number;
    side: 'buy' | 'sell'; // Or string if other values are possible from backend
    trade_id: string;
    // aggressor_side?: 'buy' | 'sell';
}

export interface FetchTradesParams {
    limit?: number;
    since_timestamp_utc?: string;
    min_volume?: number;
}


// Interfaces for Footprint Chart Data
export interface FootprintPriceLevelData {
    price: number;
    bid_volume: number;
    ask_volume: number;
    delta: number;
    total_volume: number;
}

export interface FootprintBarData {
    timestamp: string; // ISO 8601 datetime string
    open: number;
    high: number;
    low: number;
    close: number;
    total_volume: number;
    total_delta: number;
    price_levels: FootprintPriceLevelData[];
    // point_of_control_price?: number; // Optional, if backend provides
}

export interface FootprintChartData {
    exchange: string;
    symbol: string;
    timeframe: string;
    bars: FootprintBarData[];
}

export interface FetchFootprintParams {
    timeframe: string;        // e.g., "1m", "5m", "1H"
    start_time_utc?: string;  // ISO 8601 string, optional
    end_time_utc?: string;    // ISO 8601 string, optional
}


const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "/api/v1"; // Default if not set in .env

/**
 * Fetches the latest order book snapshot from the backend API.
 * @param exchange The name of the exchange.
 * @param symbol The trading symbol.
 * @returns A Promise resolving to the OrderBookSnapshot data.
 * @throws An error if the API call fails or returns a non-OK status.
 */
export async function fetchOrderBookSnapshot(
    exchange: string,
    symbol: string
): Promise<OrderBookSnapshot> {
    const url = `${API_BASE_URL}/market_data/order_book/${exchange.toLowerCase()}/${symbol.toLowerCase()}`;

    try {
        const response = await fetch(url);

        if (!response.ok) {
            let errorMessage = `Error fetching order book: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage; // Use server's error detail if available
            } catch (jsonError) {
                // Ignore if error response is not JSON
            }
            throw new Error(errorMessage);
        }

        const data: OrderBookSnapshot = await response.json();
        return data;

    } catch (error) {
        // Log the error for debugging purposes if needed console.error("fetchOrderBookSnapshot error:", error);
        throw error; // Re-throw to be handled by the calling component
    }
}


/**
 * Fetches footprint chart data from the backend API.
 * @param exchange The name of the exchange.
 * @param symbol The trading symbol.
 * @param params Parameters for fetching footprint data (timeframe, start_time_utc, end_time_utc).
 * @returns A Promise resolving to FootprintChartData.
 * @throws An error if the API call fails or returns a non-OK status.
 */
export async function fetchFootprintData(
    exchange: string,
    symbol: string,
    params: FetchFootprintParams
): Promise<FootprintChartData> {
    const queryParams = new URLSearchParams();
    queryParams.append('timeframe', params.timeframe);
    if (params.start_time_utc) {
        queryParams.append('start_time_utc', params.start_time_utc);
    }
    if (params.end_time_utc) {
        queryParams.append('end_time_utc', params.end_time_utc);
    }

    const queryString = queryParams.toString();
    const url = `${API_BASE_URL}/market_data/footprint/${exchange.toLowerCase()}/${symbol.toLowerCase()}?${queryString}`;

    try {
        const response = await fetch(url);

        if (!response.ok) {
            let errorMessage = `Error fetching footprint data: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (jsonError) {
                // Ignore if error response is not JSON
            }
            throw new Error(errorMessage);
        }

        const data: FootprintChartData = await response.json();
        return data;

    } catch (error) {
        // Log the error for debugging purposes if needed console.error("fetchFootprintData error:", error);
        throw error; // Re-throw to be handled by the calling component
    }
}


/**
 * Fetches recent trades from the backend API.
 * @param exchange The name of the exchange.
 * @param symbol The trading symbol.
 * @param params Optional parameters for filtering trades (limit, since_timestamp_utc, min_volume).
 * @returns A Promise resolving to an array of Trade objects.
 * @throws An error if the API call fails or returns a non-OK status.
 */
export async function fetchRecentTrades(
    exchange: string,
    symbol: string,
    params: FetchTradesParams = {} // Default to empty object if no params provided
): Promise<Trade[]> {
    const queryParams = new URLSearchParams();
    if (params.limit !== undefined) {
        queryParams.append('limit', params.limit.toString());
    }
    if (params.since_timestamp_utc) {
        queryParams.append('since_timestamp_utc', params.since_timestamp_utc);
    }
    if (params.min_volume !== undefined) {
        queryParams.append('min_volume', params.min_volume.toString());
    }

    const queryString = queryParams.toString();
    const url = `${API_BASE_URL}/market_data/trades/${exchange.toLowerCase()}/${symbol.toLowerCase()}${queryString ? `?${queryString}` : ''}`;

    try {
        const response = await fetch(url);

        if (!response.ok) {
            let errorMessage = `Error fetching trades: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (jsonError) {
                // Ignore if error response is not JSON
            }
            throw new Error(errorMessage);
        }

        const data: Trade[] = await response.json();
        return data;

    } catch (error) {
        // Log the error for debugging purposes if needed console.error("fetchRecentTrades error:", error);
        throw error; // Re-throw to be handled by the calling component
    }
}


/**
 * Fetches volume profile data from the backend API.
 * @param exchange The name of the exchange.
 * @param symbol The trading symbol.
 * @param params Parameters for fetching volume profile data.
 * @returns A Promise resolving to VolumeProfileData.
 * @throws An error if the API call fails or returns a non-OK status.
 */
export async function fetchVolumeProfile(
    exchange: string,
    symbol: string,
    params: FetchVolumeProfileParams
): Promise<VolumeProfileData> {
    const queryParams = new URLSearchParams();
    queryParams.append('profile_type', params.profile_type);

    if (params.date_utc) {
        queryParams.append('date_utc', params.date_utc);
    }
    if (params.start_time_utc) {
        queryParams.append('start_time_utc', params.start_time_utc);
    }
    if (params.end_time_utc) {
        queryParams.append('end_time_utc', params.end_time_utc);
    }
    if (params.tick_size !== undefined) {
        queryParams.append('tick_size', params.tick_size.toString());
    }

    const queryString = queryParams.toString();
    const url = `${API_BASE_URL}/market_data/volume_profile/${exchange.toLowerCase()}/${symbol.toLowerCase()}?${queryString}`;

    try {
        const response = await fetch(url);

        if (!response.ok) {
            let errorMessage = `Error fetching volume profile: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (jsonError) {
                // Ignore if error response is not JSON
            }
            throw new Error(errorMessage);
        }

        const data: VolumeProfileData = await response.json();
        return data;

    } catch (error) {
        // Log the error for debugging purposes if needed console.error("fetchVolumeProfile error:", error);
        throw error; // Re-throw to be handled by the calling component
    }
}


/**
 * Fetches Cumulative Volume Delta (CVD) data from the backend API.
 * @param exchange The name of the exchange.
 * @param symbol The trading symbol.
 * @param params Parameters for fetching CVD data.
 * @returns A Promise resolving to CVDChartData.
 * @throws An error if the API call fails or returns a non-OK status.
 */
export async function fetchCVDData(
    exchange: string,
    symbol: string,
    params: FetchCVDParams
): Promise<CVDChartData> {
    const queryParams = new URLSearchParams();
    queryParams.append('timeframe', params.timeframe);

    if (params.start_time_utc) {
        queryParams.append('start_time_utc', params.start_time_utc);
    }
    if (params.end_time_utc) {
        queryParams.append('end_time_utc', params.end_time_utc);
    }
    if (params.reset_condition) {
        queryParams.append('reset_condition', params.reset_condition);
    }

    const queryString = queryParams.toString();
    const url = `${API_BASE_URL}/market_data/cvd/${exchange.toLowerCase()}/${symbol.toLowerCase()}?${queryString}`;

    try {
        const response = await fetch(url);

        if (!response.ok) {
            let errorMessage = `Error fetching CVD data: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (jsonError) {
                // Ignore if error response is not JSON
            }
            throw new Error(errorMessage);
        }

        const data: CVDChartData = await response.json();
        return data;

    } catch (error) {
        // Log the error for debugging purposes if needed console.error("fetchCVDData error:", error);
        throw error; // Re-throw to be handled by the calling component
    }
}


/**
 * Fetches Advanced Delta Metrics (DVPR, DMRV) data from the backend API.
 * @param exchange The name of the exchange.
 * @param symbol The trading symbol.
 * @param params Parameters for fetching advanced delta metrics.
 * @returns A Promise resolving to AdvancedDeltaMetricsData.
 * @throws An error if the API call fails or returns a non-OK status.
 */
export async function fetchAdvancedDeltaMetrics(
    exchange: string,
    symbol: string,
    params: FetchAdvancedDeltaMetricsParams
): Promise<AdvancedDeltaMetricsData> {
    const queryParams = new URLSearchParams();
    queryParams.append('timeframe', params.timeframe);

    if (params.start_time_utc) queryParams.append('start_time_utc', params.start_time_utc);
    if (params.end_time_utc) queryParams.append('end_time_utc', params.end_time_utc);
    if (params.atr_period !== undefined) queryParams.append('atr_period', params.atr_period.toString());
    if (params.dmrv_short_ma !== undefined) queryParams.append('dmrv_short_ma', params.dmrv_short_ma.toString());
    if (params.dmrv_long_ma !== undefined) queryParams.append('dmrv_long_ma', params.dmrv_long_ma.toString());

    const queryString = queryParams.toString();
    const url = `${API_BASE_URL}/market_data/advanced_delta_metrics/${exchange.toLowerCase()}/${symbol.toLowerCase()}?${queryString}`;

    try {
        const response = await fetch(url);

        if (!response.ok) {
            let errorMessage = `Error fetching advanced delta metrics: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (jsonError) {
                // Ignore
            }
            throw new Error(errorMessage);
        }

        const data: AdvancedDeltaMetricsData = await response.json();
        return data;

    } catch (error) {
        // console.error("fetchAdvancedDeltaMetrics error:", error);
        throw error;
    }
}


/**
 * Sends features to the backend to get an absorption event outcome prediction.
 * @param features The input features for the prediction model.
 * @returns A Promise resolving to AbsorptionOutcomeOutput.
 * @throws An error if the API call fails or returns a non-OK status.
 */
export async function predictAbsorptionOutcome(
    features: AbsorptionEventInputFeatures
): Promise<AbsorptionOutcomeOutput> {
    const url = `${API_BASE_URL}/ml/predict/absorption_outcome`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(features),
        });

        if (!response.ok) {
            let errorMessage = `Error predicting absorption outcome: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (jsonError) {
                // Ignore
            }
            throw new Error(errorMessage);
        }

        const data: AbsorptionOutcomeOutput = await response.json();
        return data;

    } catch (error) {
        // console.error("predictAbsorptionOutcome error:", error);
        throw error;
    }
}


/**
 * Sends features to the backend to get a breakout viability prediction.
 * @param features The input features for the prediction model.
 * @returns A Promise resolving to BreakoutViabilityOutput.
 * @throws An error if the API call fails or returns a non-OK status.
 */
export async function predictBreakoutViability(
    features: BreakoutViabilityInputFeatures
): Promise<BreakoutViabilityOutput> {
    const url = `${API_BASE_URL}/ml/predict/breakout_viability`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(features),
        });

        if (!response.ok) {
            let errorMessage = `Error predicting breakout viability: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (jsonError) {
                // Ignore
            }
            throw new Error(errorMessage);
        }

        const data: BreakoutViabilityOutput = await response.json();
        return data;

    } catch (error) {
        // console.error("predictBreakoutViability error:", error);
        throw error;
    }
}


/**
 * Sends features to the backend to get a momentum sustainability prediction.
 * @param features The input features for the prediction model.
 * @returns A Promise resolving to MomentumSustainabilityOutput.
 * @throws An error if the API call fails or returns a non-OK status.
 */
export async function predictMomentumSustainability(
    features: MomentumSustainabilityInputFeatures
): Promise<MomentumSustainabilityOutput> {
    const url = `${API_BASE_URL}/ml/predict/momentum_sustainability`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(features),
        });

        if (!response.ok) {
            let errorMessage = `Error predicting momentum sustainability: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (jsonError) {
                // Ignore
            }
            throw new Error(errorMessage);
        }

        const data: MomentumSustainabilityOutput = await response.json();
        return data;

    } catch (error) {
        // console.error("predictMomentumSustainability error:", error);
        throw error;
    }
}
