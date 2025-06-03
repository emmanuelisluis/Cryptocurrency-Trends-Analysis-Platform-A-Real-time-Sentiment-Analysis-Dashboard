# Backend

This directory contains the Python FastAPI backend for the Crypto Dashboard.

It provides API endpoints for:
- Real-time market data (order book, trades) - though ingestion is real-time, API provides snapshots or recent data.
- Aggregated analytical data (footprint charts, volume profiles, CVD, advanced delta metrics).
- (Simulated) ML model predictions (momentum sustainability, breakout viability, absorption outcome).
- Data ingestion from exchanges (e.g., Binance WebSockets).
- Status and health checks.

## Core Technologies
- Python 3.10+
- FastAPI (for RESTful APIs)
- SQLAlchemy (for database interaction)
- TimescaleDB (for time-series data storage)
- Pandas (for data manipulation and analysis)
- Pydantic (for data validation and settings management)
- Uvicorn (ASGI server)
- Poetry (dependency management)

For detailed setup instructions, architecture, and component descriptions, please see the [main backend documentation here](../docs/backend_setup.md).

To run the backend (which includes data ingestion and the API server):
1. Ensure all dependencies are installed: `poetry install` (from this `backend` directory).
2. Ensure your `.env` file is configured, especially `DATABASE_URL`.
3. Run database initializations if it's the first time: `poetry run python -m app.db.init_db`
4. Navigate to the project root directory (one level above this `backend` directory).
5. Execute: `poetry -C backend run python run_ingestion.py`
   (This command tells Poetry to use the `backend`'s virtual environment but runs the script from the project root).

The API documentation (Swagger UI) will typically be available at `http://localhost:8000/docs` when the server is running.
The main application log, including data ingestion status, will be visible in the console where `run_ingestion.py` is executed.
The `run_ingestion.py` script handles both starting the FastAPI/Uvicorn server and initializing the data ingestion services in the background.
