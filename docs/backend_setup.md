# Backend Setup and Core Components

This document provides instructions for setting up the backend of the Crypto Dashboard and an overview of its core components.

## 1. Setup Instructions

*   **Prerequisites:**
    *   Python (version 3.10 or higher recommended).
    *   Poetry for Python package management and virtual environments. (Install from [https://python-poetry.org/](https://python-poetry.org/))
    *   A running TimescaleDB instance. TimescaleDB is an extension for PostgreSQL. Ensure PostgreSQL is installed and the TimescaleDB extension is enabled on your target database.
        *   See TimescaleDB installation: [https://docs.timescale.com/install/latest/](https://docs.timescale.com/install/latest/)
*   **Cloning the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>/backend
    ```
*   **Installing Dependencies:**
    *   Navigate to the `backend` directory.
    *   Poetry will manage project dependencies defined in `pyproject.toml`.
    ```bash
    poetry install
    ```
    This command creates a virtual environment (if one doesn't exist) and installs all necessary packages (e.g., FastAPI, Uvicorn, SQLAlchemy, Pandas, Psycopg2 for PostgreSQL).
*   **Environment Variables Setup:**
    *   The backend uses a `.env` file for configuration.
    *   Create a `.env` file in the `backend` directory by copying from a template if provided (e.g., `.env.example`) or creating it manually.
    *   Key variable: `DATABASE_URL`. This is the connection string for your TimescaleDB instance.
        Example: `DATABASE_URL=postgresql://your_db_user:your_db_password@your_db_host:your_db_port/your_db_name`
        (Replace placeholders with your actual database credentials and details).
    *   Other potential variables: API keys for exchanges (if used beyond public data), ML model paths (though currently simulated).
*   **Database Initialization (Schema Creation):**
    *   The `backend/app/db/init_db.py` script is provided to create database tables and TimescaleDB hypertables based on SQLAlchemy models.
    *   Ensure your `DATABASE_URL` in `.env` is correctly configured and the database is accessible.
    *   Run from the `backend` directory using Poetry:
        ```bash
        poetry run python -m app.db.init_db
        ```
        (The `-m` flag runs the script as a module, ensuring correct Python path resolution for imports within the `app` package).
    *   This step only needs to be run once initially, or if you drop and want to recreate the tables. For schema changes after initial setup (evolutions), a proper migration tool like Alembic would be used in a production environment (Alembic setup is not part of the current project state).
*   **Starting the Backend Server & Data Ingestion:**
    *   The main entry point for running the application (FastAPI server and data ingestion service) is `run_ingestion.py`, located in the project root (`/app`, one level above `backend`).
    *   From the `/app` directory (project root):
        ```bash
        # Ensure you are in the /app directory (parent of /backend)
        cd ..
        poetry -C backend run python run_ingestion.py
        ```
        *   `poetry -C backend run ...`: This tells Poetry to use the context of the `backend` subdirectory (where `pyproject.toml` is located) to find the virtual environment and dependencies, but executes the `python run_ingestion.py` command from the current directory (`/app`).
    *   This script will:
        1.  Initialize the database (calling `initialize_database()` from `init_db.py`).
        2.  Start the Uvicorn server for the FastAPI application (defined in `backend/main.py`).
        3.  The FastAPI application, via its lifespan events, will initialize and start the `DataIngestionService` (e.g., `BinanceWebSocketClient`) in the background to connect to exchanges and start ingesting data.
    *   The API server will typically run on `http://localhost:8000` (or as configured by `APP_HOST`/`APP_PORT` in `.env`).

## 2. Core Backend Components

*   **`run_ingestion.py` (in `/app` - project root):**
    *   Main executable script.
    *   Orchestrates database initialization and Uvicorn server startup.
*   **`backend/main.py`:**
    *   Defines the main FastAPI `app` instance.
    *   Includes all API routers from `api/endpoints/`.
    *   Manages the lifecycle of background services (like `DataIngestionService`) using FastAPI's lifespan events (`@app.on_event("startup")`, `@app.on_event("shutdown")`).
*   **Configuration (`backend/app/core/config.py`):**
    *   Uses `pydantic-settings` for loading and validating application settings from environment variables and the `.env` file.
    *   Includes `DATABASE_URL`, API keys (placeholders), ML model paths (placeholders), UI-related defaults.
*   **Database (`backend/app/db/`):**
    *   `session.py`: Configures the SQLAlchemy engine (`create_engine`) and provides `SessionLocal` for creating database sessions. Includes a `get_db` dependency for FastAPI request-scoped sessions and `create_session` for background tasks.
    *   `models.py`: Defines all SQLAlchemy ORM models (e.g., `TradeDB`, `OrderBookSnapshotDB`, `TickerDB`), which map to database tables. Specifies table names, columns, relationships, and indexes.
    *   `init_db.py`: Contains functions (`create_all_tables`, `create_hypertables`, `initialize_database`) to set up the database schema based on the models in `models.py`.
*   **Services (`backend/app/services/`):** Contain the business logic of the application.
    *   `data_ingestion_service.py` (`DataIngestionService`): Manages instances of exchange clients (e.g., `BinanceWebSocketClient`). Responsible for starting/stopping data feeds and passing received data to a handler (e.g., `db_data_handler` for database storage).
    *   `exchange_clients/binance_client.py` (`BinanceWebSocketClient`): Connects to Binance WebSocket streams, parses incoming JSON data, normalizes it into Pydantic models, and passes it to a callback. Includes status tracking and reconnection logic.
    *   `order_book_service.py`: Contains logic for querying and returning processed order book data, including imbalances and OBDG metrics.
    *   `trade_service.py`: Logic for querying and returning recent trade data with filtering.
    *   `footprint_service.py` (`FootprintService`): Core logic for generating footprint chart data. Fetches trades, aggregates them into bars using Pandas, and calculates bid/ask volume at each price level within each bar.
    *   `volume_profile_service.py` (`VolumeProfileService`): Calculates Volume Profile (volume at price) for specified periods or ranges, including POC and VA, using Pandas for aggregation.
    *   `delta_analysis_service.py` (`DeltaAnalysisService`): Calculates CVD and advanced delta metrics (DVPR, DMRV). Uses `FootprintService` to get bar delta data and then performs further calculations (e.g., ATR, moving averages) using Pandas.
    *   `ml_prediction_service.py` (`MLPredictionService`): Manages simulated ML models. Includes an `MLModel` wrapper for placeholder loading and prediction logic. Provides methods to get predictions for defined ML tasks (Momentum Sustainability, Breakout Viability, Absorption Outcome).
*   **API Endpoints (`backend/app/api/endpoints/`):** Define the HTTP routes.
    *   `market_data.py`: Contains routes for all market data related queries (order book, trades, footprint, volume profile, CVD, advanced delta metrics).
    *   `ml_predictions.py`: Contains routes for ML model predictions.
    *   `status.py`: Contains routes for checking data feed health and application status.
    *   Uses FastAPI `APIRouter`, Pydantic models for request body validation and response serialization. Depends on service classes for business logic.
*   **Pydantic Models (`backend/app/models/`):**
    *   `exchange_data.py`: Pydantic models for raw/normalized data from exchange streams (e.g., `TradeData`, `OrderBookData`). Used internally by ingestion services.
    *   `order_book_models.py`, `trade_models.py`, `footprint_models.py`, `volume_profile_models.py`, `delta_analysis_models.py`: Pydantic models defining the structure of API responses for different market data endpoints.
    *   `ml_prediction_models.py`: Pydantic models for ML feature inputs and prediction outputs.
    *   `status_models.py`: Pydantic models for the feed health status API response.
*   **ML Model Integration (`backend/app/ml_models/`, `backend/app/services/ml_prediction_service.py`):**
    *   `ml_models/` is the designated directory for storing serialized model files (e.g., `.pkl`). Currently, no actual models are present.
    *   `MLPredictionService` simulates model loading and prediction. The structure is designed to allow for easy replacement with actual model loading and inference code.
*   **Utilities (`backend/app/utils/`):**
    *   `time_utils.py`: Helper functions for parsing timeframe strings and mapping them to Pandas frequency strings.
    *   `technical_analysis_utils.py`: Contains functions for technical calculations like ATR.
*   **Global State (`backend/app/globals.py`):** Manages shared instances, such as the `DataIngestionService`, making it accessible to both the main application startup (for starting ingestion) and API endpoints (for status checks).
```
