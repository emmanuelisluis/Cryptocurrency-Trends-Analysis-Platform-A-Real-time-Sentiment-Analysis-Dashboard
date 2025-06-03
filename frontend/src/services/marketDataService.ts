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
    imbalances?: ImbalanceAtDepth[]; // Added this field
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
