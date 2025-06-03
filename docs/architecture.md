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
     *   **Technology Stack:** Python 3.10+, FastAPI, SQLAlchemy (ORM), TimescaleDB (PostgreSQL extension), Pandas (for data analysis & manipulation), Pydantic (for data validation & settings), Uvicorn (ASGI server).
     *   **Directory Structure (`backend/app/`):**
         *   `main.py`: FastAPI app initialization, router inclusion, lifespan events.
         *   `core/`: Configuration (`config.py`), core dependencies.
         *   `db/`: Database models (`models.py`), session management (`session.py`), initialization scripts (`init_db.py`).
         *   `models/`: Pydantic models for API requests/responses and internal data structures.
         *   `services/`: Business logic layer, data processing, interactions between components.
         *   `api/endpoints/`: FastAPI routers defining API paths and request handlers.
         *   `utils/`: Shared utility functions (e.g., time parsing, technical analysis).
         *   `ml_models/`: (Conceptual) Intended location for serialized ML model files.
     *   **Core Services & Interactions:**
         *   `DataIngestionService`: Manages `BinanceWebSocketClient` (or other exchange clients). Normalizes data from exchanges and uses `db_data_handler` (which creates its own DB session) to store data in TimescaleDB.
         *   `OrderBookService`, `TradeService`: Provide data directly from database queries, formatting results using Pydantic models defined in `models/order_book_models.py` and `models/trade_models.py`.
         *   `FootprintService`: Fetches raw trades (via `TradeDB`), then uses Pandas to perform time-based resampling and aggregation to construct footprint bars.
         *   `VolumeProfileService`: Similar to `FootprintService`, fetches trades and uses Pandas to group by price and calculate volume distribution, POC, and VA.
         *   `DeltaAnalysisService`: Leverages `FootprintService` to get bar-level data (especially `total_delta`). It then performs further calculations (CVD accumulation, ATR via `technical_analysis_utils.py`, MAs) using Pandas to derive CVD, DVPR, and DMRV metrics.
         *   `MLPredictionService`: Contains an `MLModel` wrapper that simulates loading and prediction. It takes Pydantic feature models, converts them to Pandas DataFrames (mimicking real model input needs), and returns (simulated) Pydantic output models.
*   **Database Schema (`db/models.py`):**
         *   `TradeDB`: Stores individual trade records. Key columns: `timestamp`, `symbol`, `exchange`, `trade_id`, `price`, `volume`, `side`, `aggressor_side`. Hypertable on `timestamp`.
         *   `OrderBookSnapshotDB`: Stores snapshots of order book levels (bids/asks as JSONB). Key columns: `timestamp`, `symbol`, `exchange`, `bids`, `asks`, `last_update_id`. Hypertable on `timestamp`.
         *   `TickerDB`: Stores summary price/volume information. Key columns: `timestamp`, `symbol`, `exchange`, `last_price`, `volume_24h`. Hypertable on `timestamp`.
         *   Hypertables are created using `SELECT create_hypertable(...)` in `db/init_db.py`.
*   **API Design (`api/endpoints/`):**
         *   Uses FastAPI routers for modularity. Pydantic models are used for request body validation and defining `response_model` for automatic serialization and API documentation (Swagger/OpenAPI).
    *   Key endpoint groups:
             *   `/market_data/`: Serves order book data, recent trades, footprint charts, volume profiles, CVD, and advanced delta metrics.
             *   `/ml/`: Exposes endpoints for each (simulated) ML prediction type (momentum, breakout, absorption).
             *   `/status/`: Provides health check for data ingestion feeds.
     *   **Configuration (`core/config.py`):** `pydantic-settings` loads configuration from environment variables or `.env` file, including `DATABASE_URL` and paths to ML model files.

## 3. Frontend Architecture
     *   **Technology Stack:** React (with Hooks), TypeScript, Recharts (for charting), `react-router-dom` (for navigation), `react-datepicker` (for date inputs), CSS (per-component or global).
     *   **Directory Structure (`frontend/src/`):**
         *   `App.tsx`: Main application component, sets up router and global context.
         *   `index.tsx`: Renders `App` into the DOM.
         *   `contexts/`: React Context API for global state (e.g., `GlobalMarketContext.tsx`).
         *   `components/`: Reusable UI components.
             *   `layout/`: Components like `GlobalControlsBar.tsx`.
             *   `market/`: Charting and data display components (e.g., `FootprintChart.tsx`, `OrderBookDepthChart.tsx`).
         *   `pages/`: Top-level page components (e.g., `MarketViewPage.tsx`).
         *   `services/`: API interaction layer (`marketDataService.ts`).
         *   `models/` (implicit via service interfaces): TypeScript interfaces matching backend Pydantic models for type safety.
     *   **Core Components & Interactions:**
         *   `GlobalMarketContext`: Provides shared state for `selectedExchange`, `selectedSymbol`, and `selectedGlobalTimeframe`.
         *   `GlobalControlsBar`: Uses context to display and update global selections.
         *   `MarketViewPage`: Consumes global context and passes `exchange`, `symbol`, and `globalTimeframe` to its child chart components. Uses a `chartKey` to ensure charts re-render on asset/timeframe change.
         *   **Chart Components** (e.g., `FootprintChart`, `CVDChart`):
             *   Receive `exchange`, `symbol`, `globalTimeframe` as props.
             *   Manage their own local state for specific parameters (e.g., date ranges, indicator periods, ML prediction results).
             *   Use `useEffect` hooks to:
                 *   Synchronize their internal timeframe state with the `globalTimeframe` prop.
                 *   Fetch data from `marketDataService.ts` when relevant props or parameters change.
             *   Render visualizations using `Recharts`.
             *   `FootprintChart` additionally handles user clicks on bars/cells to trigger ML predictions by collecting features and calling relevant functions in `marketDataService.ts`.
         *   `marketDataService.ts`: Centralizes all `fetch` calls to backend API endpoints. Defines TypeScript interfaces for request payloads and response data, ensuring type safety and aligning with backend Pydantic models.
     *   **State Management:**
         *   `GlobalMarketContext` for globally shared selections (exchange, symbol, timeframe).
         *   Local component state (`useState`, `useCallback`, `useMemo`) within each chart/tool for managing UI parameters, fetched data, loading/error states, and user interactions like drawing or ML prediction results.
*   **ML Integration:**
         *   User interaction (e.g., click on a footprint chart bar/cell) in a component like `FootprintChart.tsx` triggers a specific ML prediction.
         *   The component gathers necessary features from its current data (e.g., bar delta, volume, timestamp, clicked price level).
         *   A call is made to the corresponding prediction function in `marketDataService.ts`.
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
