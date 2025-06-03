# Technical Architecture

This document outlines the technical architecture of the Crypto Dashboard application.

## 1. Overview
*   The Crypto Dashboard is a web application designed for advanced market analysis, providing real-time data visualizations, order flow tools, and (simulated) ML-driven insights.
*   It features a React/TypeScript frontend for a responsive user experience and a Python/FastAPI backend for efficient data processing and API delivery.
*   TimescaleDB (a PostgreSQL extension for time-series data) is used for storing market data.
*   **High-Level Diagram:**
    ```
    [User via Browser] <--> [React Frontend (TypeScript, Recharts)]
           ^
           | (HTTPS/WSS - REST/WebSocket API Calls)
           v
    [FastAPI Backend (Python)] <--> [TimescaleDB (PostgreSQL)]
           ^                                      ^
           | (WebSocket)                          | (Data Storage)
           v                                      |
    [External Exchanges (e.g., Binance API)] ----(Raw Market Data Ingestion)
    ```

## 2. Backend Architecture
*   **Technology Stack:** Python 3.10+, FastAPI, SQLAlchemy (with TimescaleDB dialect for hypertables), Pydantic, Pandas, Uvicorn.
*   **Core Services:**
    *   `DataIngestionService`: Connects to exchange WebSockets (e.g., Binance), normalizes trade, order book, and ticker data into Pydantic models, and stores them in TimescaleDB.
    *   `OrderBookService`: Provides API endpoints to retrieve the latest order book snapshots, including calculated imbalances and Order Book Depth Gradient (OBDG) metrics.
    *   `TradeService`: Offers API endpoints for fetching recent trades with filtering capabilities (limit, timestamp, volume).
    *   `FootprintService`: Aggregates raw trade data (especially aggressor side) into footprint bars (time-based, showing bid/ask volume at each price level). Exposes this data via an API.
    *   `VolumeProfileService`: Calculates Volume Profile (total volume at price levels over a specified range or period), including Point of Control (POC) and Value Area (VA). Served via API.
    *   `DeltaAnalysisService`:
        *   Calculates Cumulative Volume Delta (CVD) based on total deltas from footprint bars, with options for daily reset.
        *   Calculates advanced delta metrics: Delta Volume Pressure Ratio (DVPR) and Delta Moving Average Rate of Change (DMRV), using ATR and moving averages on bar deltas. Served via API.
    *   `MLPredictionService`: Manages (simulated) ML models. Provides a framework to load models and serve predictions via API endpoints for:
        *   Momentum Sustainability
        *   Breakout Viability
        *   Absorption Event Outcome
*   **Database Schema (`db/models.py`):**
    *   `TradeDB`: Stores individual trades, including price, volume, side, timestamp, exchange, symbol, trade ID, and aggressor side. Hypertable on `timestamp`.
    *   `OrderBookSnapshotDB`: Stores periodic snapshots of the order book (bids/asks arrays as JSONB), timestamp, exchange, symbol. Hypertable on `timestamp`.
    *   `TickerDB`: Stores ticker data (last price, 24h volume, etc.). Hypertable on `timestamp`.
    *   (Other potential tables for user data, settings, etc., if features expand).
*   **API Design (`api/endpoints/`):**
    *   RESTful principles are followed.
    *   FastAPI used for high performance and automatic data validation/serialization with Pydantic.
    *   Key endpoint groups:
        *   `/market_data/`: For order book, trades, footprint, volume profile, CVD, advanced delta.
        *   `/ml/`: For ML predictions.
        *   `/status/`: For application health/feed status.
*   **Configuration (`core/config.py`):** Pydantic-settings for managing application settings via environment variables and `.env` files (e.g., `DATABASE_URL`, ML model paths, API keys).

## 3. Frontend Architecture
*   **Technology Stack:** React, TypeScript, Recharts (for charting), `react-router-dom` (for navigation), `react-datepicker`.
*   **Core Components (Conceptual Groups):**
    *   **Layout & Navigation (`App.tsx`, `pages/MarketViewPage.tsx`, `components/layout/GlobalControlsBar.tsx`):**
        *   `App.tsx`: Main application shell, sets up routing and global context providers.
        *   `MarketViewPage.tsx`: Primary view hosting all market analysis charts and tools.
        *   `GlobalControlsBar.tsx`: Allows users to select global exchange, symbol, and timeframe.
    *   **Data Display Widgets (`components/market/`):**
        *   `OrderBookDepthChart.tsx`: Displays order book depth, imbalances, and OBDG.
        *   `TimeAndSalesLog.tsx`: Shows a log of recent trades with filtering and large trade highlighting.
        *   `FootprintChart.tsx`: Renders footprint bars with bid/ask volume per price, delta, POC, imbalances, unfinished auctions, and integrates ML prediction triggers.
        *   `VolumeProfileChart.tsx`: Displays volume profile as a horizontal histogram with POC and VA.
        *   `CVDChart.tsx`: Shows Cumulative Volume Delta as a line chart with divergence drawing tools.
        *   `AdvancedDeltaMetricsChart.tsx`: Displays DVPR and DMRV as line charts.
    *   **Services (`services/marketDataService.ts`):** Contains functions to fetch data from all backend API endpoints using the `fetch` API. TypeScript interfaces define data structures.
    *   **State Management:**
        *   `GlobalMarketContext.tsx`: Manages globally selected exchange, symbol, and timeframe.
        *   Component-level state (`useState`, `useCallback`, `useMemo`): Used extensively within each chart/tool for managing local UI state, fetched data, and parameters.
*   **ML Integration:**
    *   The `FootprintChart.tsx` allows users to trigger ML predictions by clicking on bars (for momentum, breakout) or price cells (for absorption).
    *   Collected features are sent to the backend via `marketDataService.ts`.
    *   Prediction results are displayed in dedicated UI sections within the `FootprintChart`.

## 4. Data Flow
*   **Real-time Data Ingestion:**
    1.  Exchange WebSocket (e.g., Binance) streams raw market data (trades, order book updates, tickers).
    2.  `BinanceWebSocketClient` (managed by `DataIngestionService`) receives, parses, and normalizes this data into Pydantic models.
    3.  `DataIngestionService`'s `db_data_handler` converts Pydantic models to SQLAlchemy `TradeDB`, `OrderBookSnapshotDB`, `TickerDB` models.
    4.  Data is committed to TimescaleDB, leveraging hypertable capabilities.
*   **Client-API Interaction (for Charts & Analysis):**
    1.  User interacts with frontend (e.g., selects symbol/timeframe on `GlobalControlsBar`, or sets parameters within a chart component).
    2.  React component (e.g., `FootprintChart.tsx`) triggers a data fetch using a function from `marketDataService.ts`.
    3.  `marketDataService.ts` makes an HTTP GET or POST request to the relevant FastAPI backend endpoint.
    4.  FastAPI endpoint receives the request, validates parameters (via Pydantic).
    5.  The endpoint calls the appropriate service method (e.g., `FootprintService.get_footprint_data`).
    6.  The service method queries TimescaleDB (often using Pandas for complex aggregations like in Footprint, Volume Profile, Advanced Delta).
    7.  Data is processed, aggregated, and structured into Pydantic response models.
    8.  FastAPI automatically serializes the Pydantic response model to JSON and sends it back to the frontend.
    9.  The frontend service function receives the JSON, which is then used to update React component state, causing a re-render to display the new data/chart.
*   **ML Prediction Flow:**
    1.  User clicks on a specific element in `FootprintChart.tsx` (bar or price cell).
    2.  The click handler gathers relevant features from the local chart data.
    3.  `marketDataService.ts` sends these features in a POST request to the appropriate `/api/v1/ml/predict/...` endpoint.
    4.  `MLPredictionService` receives the features, converts them to a format suitable for the (simulated) model.
    5.  The (simulated) model "predicts" an outcome.
    6.  The prediction is returned to the frontend and displayed.

## 5. ML Integration Strategy
*   **Current Approach:**
    *   The backend's `MLPredictionService` defines a simple `MLModel` wrapper.
    *   This wrapper simulates model loading (no actual `.pkl` files are loaded in the current phase) and prediction.
    *   FastAPI endpoints are created for each (simulated) model type (Momentum Sustainability, Breakout Viability, Absorption Outcome).
    *   The frontend triggers predictions based on user interaction (e.g., clicking a footprint bar) and sends relevant features.
*   **Input Features (Examples):**
    *   **Momentum Sustainability:** `bar_timestamp`, `bar_delta`, `bar_volume`, `recent_cvd_slope` (optional), `market_volatility_atr` (optional).
    *   **Breakout Viability:** `breakout_price_level`, `bar_timestamp_breakout_attempt`, `volume_at_breakout_bar`, `delta_at_breakout_bar`, `recent_volatility_atr` (optional).
    *   **Absorption Outcome:** `event_timestamp`, `absorption_price_level`, `volume_at_absorption_level`, `delta_at_absorption_level`, `total_bar_volume`, `total_bar_delta`.
*   **Future Considerations for Real Model Deployment:**
    *   **Model Training Pipeline:** Separate offline process for data collection, feature engineering, model training, and evaluation.
    *   **Model Serialization:** Saving trained models using `joblib`, `pickle`, or framework-specific formats (e.g., TensorFlow SavedModel, PyTorch `torch.save`).
    *   **Model Loading:** Implementing actual model loading in `MLModel._load_model()`.
    *   **Feature Engineering:** Robust feature extraction and preprocessing logic will be needed, both for training and inference. Some features might be computed on-the-fly by the backend service before prediction.
    *   **Performance:** Inference time for complex models. Consider asynchronous prediction or dedicated inference servers if models are heavy.
    *   **Versioning:** Proper versioning for models and tracking which version made a prediction.
    *   **Monitoring:** Logging model inputs, outputs, and performance metrics.
```
