# Crypto Order Flow Analysis Dashboard

## Overview

This project is a high-performance, interactive cryptocurrency dashboard focused on Order Flow Analysis (OFA). It aims to provide traders with advanced tools and visualizations to analyze market dynamics, including real-time order book depth, trade flows, footprint charts, and ML-driven predictive overlays.

## Key Features

*   **Real-time Data Ingestion:**
    *   Binance: L2 Order Book (Depth Stream), Trades, Ticker data.
*   **Advanced Order Book Visualization:**
    *   Interactive Order Book Depth Chart.
    *   Real-time Imbalance indicators at multiple depth levels.
    *   Order Book Depth Gradient (OBDG) statistics.
*   **Enhanced Time & Sales Log:**
    *   Filterable by trade size and time.
    *   Highlighting of large trades.
*   **Footprint Charts:**
    *   Detailed bid/ask volume per price level.
    *   Bar Delta, Cumulative Delta.
    *   Point of Control (POC).
    *   Value Area (VA).
    *   Identification of imbalances and unfinished auctions.
*   **Volume Profile:**
    *   Configurable for Daily, Weekly, Monthly, or custom Range profiles.
    *   POC and Value Area highlighting.
*   **Core Delta Analysis:**
    *   Bar Delta, Cumulative Bar Delta.
    *   Cumulative Volume Delta (CVD) with user-drawable divergence lines.
    *   Delta-Volume Profile Ratio (DVPR).
    *   Delta-Mean Reversion Bands (DMRV).
*   **ML Predictive Overlays (Simulated):**
    *   Momentum Sustainability Score.
    *   Breakout Viability Probability.
    *   Absorption Event Outcome Classification (Reversal, Continuation, Consolidation).
*   **Crypto News Aggregation & (Simulated) Sentiment Analysis Section:**
    *   Dedicated page for viewing latest crypto news.
    *   Per-article (simulated) sentiment analysis (Positive, Negative, Neutral).
*   **Global Market & Timeframe Selection:**
    *   Context-aware controls for selecting exchange, trading symbol, and global chart timeframe.
*   **Dockerized Environment:**
    *   Multi-container setup using Docker Compose for simplified local development, testing, and deployment.

## Tech Stack

*   **Backend:** Python, FastAPI, SQLAlchemy, TimescaleDB, Pandas, Uvicorn
*   **Frontend:** React, TypeScript, Recharts, CSS
*   **Data Ingestion:** Python, WebSockets
*   **Containerization:** Docker, Docker Compose

## Getting Started

### Prerequisites

*   Docker Engine
*   Docker Compose
*   Node.js (latest LTS recommended for frontend development if not using Docker exclusively)
*   Python (latest 3.10+ recommended for backend development if not using Docker exclusively)
*   Poetry (for Python dependency management if developing backend locally)

### Setup & Running

*   **For Backend setup (local development without Docker):**
    See [docs/backend_setup.md](./docs/backend_setup.md).
*   **For Frontend setup (local development without Docker):**
    See [docs/frontend_setup.md](./docs/frontend_setup.md).
*   **For running the entire application stack using Docker Compose (recommended for local development and testing):**
    See [docs/deployment.md](./docs/deployment.md) for instructions on building and running the Docker containers.

## Documentation

For more detailed information on architecture, setup, usage, and API endpoints, please refer to the main documentation portal:
[docs/README.md](./docs/README.md)

<!-- Add project screenshots or GIFs here when available -->

## Contributing

Contributions are welcome! Please refer to `CONTRIBUTING.md` (to be created) for guidelines.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
