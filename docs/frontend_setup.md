# Frontend Setup and Core Components

This document provides instructions for setting up the frontend of the Crypto Dashboard and an overview of its core components.

## 1. Setup Instructions

*   **Prerequisites:**
    *   Node.js (LTS version recommended, e.g., 18.x or 20.x).
    *   `npm` (usually comes with Node.js) or `yarn`.
*   **Cloning the Repository:** (If not already done)
    ```bash
    git clone <repository_url>
    cd <repository_name>/frontend
    ```
*   **Navigating to `frontend/` Directory:**
    *   All frontend commands should be run from the `frontend/` directory.
    ```bash
    cd frontend
    ```
*   **Installing Dependencies:**
    *   The frontend uses `npm` (or `yarn`) for package management, defined in `package.json`.
    ```bash
    npm install
    # OR
    # yarn install
    ```
    This command installs React, Recharts, React Router, TypeScript, and other necessary libraries.
    *Note: During development in some sandboxed environments, `npm install` commands for specific libraries like `recharts`, `react-datepicker`, and `react-router-dom` encountered timeouts. In a standard local development setup with proper internet access, these should install correctly.*
*   **Starting the Development Server:**
    ```bash
    npm start
    # OR
    # yarn start
    ```
    This runs the app in development mode. Open [http://localhost:3000](http://localhost:3000) (or another port if 3000 is busy) to view it in your browser. The page will reload if you make edits.
*   **Environment Variables:**
    *   The frontend can be configured using environment variables, typically defined in a `.env` file in the `frontend/` directory.
    *   A key variable is `REACT_APP_API_BASE_URL`, which specifies the base URL for the backend API.
        *   Default used in `marketDataService.ts`: `/api/v1`. This assumes the frontend is served from the same domain as the backend, or a reverse proxy is configured to route `/api/v1` requests to the backend.
        *   For local development where backend runs on `http://localhost:8000` and frontend on `http://localhost:3000`, you might set `REACT_APP_API_BASE_URL=http://localhost:8000/api/v1` in a `.env` file in the `frontend` directory. This requires CORS to be configured on the backend.
    *   Create `.env` by copying `.env.example` (if provided) or manually. Standard `create-react-app` environment variable rules apply (must start with `REACT_APP_`).

## 2. Core Frontend Components

*   **`index.tsx`:** The main entry point of the React application. It renders the `App` component, wrapped with necessary context providers (like `GlobalMarketProvider`), into the root DOM element.
*   **`App.tsx` & Routing:**
    *   The main application shell component (`AppContent` wrapped by `App` which provides contexts).
    *   Sets up `GlobalMarketProvider` for global state management of selected exchange, symbol, and timeframe.
    *   Uses `react-router-dom` for client-side navigation. Defines routes to main pages (e.g., a `HomePage` and the `MarketViewPage`).
    *   Includes basic application layout structure like global navigation links (e.g., in `App-nav`) and a footer.
*   **Contexts (`frontend/src/contexts/`):**
    *   `GlobalMarketContext.tsx`: Manages and provides globally selected `selectedExchange`, `selectedSymbol`, and `selectedGlobalTimeframe` using React Context. This state is accessible by any component within the `GlobalMarketProvider` via the `useGlobalMarket` custom hook. This allows various charts and controls to synchronize with a single source of truth for the current market context.
*   **Layout Components (`frontend/src/components/layout/`):**
    *   `GlobalControlsBar.tsx`: A persistent bar, typically displayed at the top of the `MarketViewPage`. It contains dropdown selectors for users to choose the global exchange, symbol, and analysis timeframe. It interacts with the `GlobalMarketContext` to display and update these selections.
*   **Pages (`frontend/src/pages/`):**
    *   `MarketViewPage.tsx`: The primary page for displaying all market analysis charts and tools. It consumes the `GlobalMarketContext` to get the current market selection and passes these (exchange, symbol, global timeframe) as props to the various chart components. It arranges these components in a responsive grid-like layout using CSS flexbox (`market-data-layout`, `market-data-row`).
*   **Chart & Data Display Components (`frontend/src/components/market/`):** These are the core analytical tools.
    *   `OrderBookDepthChart.tsx`: Visualizes order book depth using Recharts Area charts. Displays aggregated imbalance statistics at various depth levels and Order Book Depth Gradient (OBDG) data. Polls the backend `/order_book` endpoint for live updates.
    *   `TimeAndSalesLog.tsx`: Shows a chronological list ("tape") of recent trades. Features include filtering by trade limit and minimum volume, and highlighting of large trades based on a user-configurable threshold. Polls the backend `/trades` endpoint.
    *   `FootprintChart.tsx`: A complex component that renders footprint charts using a custom Recharts configuration (BarChart with Customized cells). It displays bid volume vs. ask volume at each price level within time-based bars. Visual cues include Delta per price, Total Bar Delta, Point of Control (POC), significant bid/ask imbalances at price levels, and potential unfinished auctions. Users can select timeframe and date range. This chart also integrates ML prediction triggers:
        *   Clicking a full bar can trigger Momentum Sustainability and Breakout Viability predictions.
        *   Clicking an individual price cell within a bar can trigger Absorption Outcome predictions.
        *   Prediction results (simulated) are displayed in a dedicated section.
    *   `VolumeProfileChart.tsx`: Displays volume profile as a horizontal bar chart using Recharts (`layout="vertical"`). Shows total volume traded at each price level over a user-selected period (daily, weekly, monthly, or custom range). Highlights POC and Value Area (VA).
    *   `CVDChart.tsx` (Cumulative Volume Delta): Renders CVD as a line chart (Recharts). Allows selection of timeframe for underlying bar deltas, date range, and CVD reset condition (none or daily). Includes a user-interactive feature for drawing divergence lines on the chart.
    *   `AdvancedDeltaMetricsChart.tsx`: Displays DVPR (Delta Volume Pressure Ratio) and DMRV (Delta Moving Average Rate of Change/Value) in separate line charts (Recharts). Allows user configuration of timeframe, date range, and parameters like ATR period and DMRV moving average periods.
*   **API Service (`frontend/src/services/marketDataService.ts`):**
    *   Centralizes all asynchronous functions responsible for making API calls to the backend.
    *   Uses the browser's `fetch` API to interact with the backend FastAPI endpoints.
    *   Defines comprehensive TypeScript interfaces for all API request parameters and response payloads, ensuring type safety throughout the frontend application. This includes interfaces for order book data, trades, footprint data, volume profiles, CVD, advanced delta metrics, and all ML prediction inputs/outputs.
    *   Handles basic error checking for API responses (e.g., `!response.ok`).
*   **Styling:**
    *   Each major component typically has an associated CSS file (e.g., `FootprintChart.css`, `GlobalControlsBar.css`) for specific styles.
    *   Global or shared styles are present in `App.css` and `index.css`.
    *   The project uses standard CSS without pre-processors like SASS/LESS or utility-first frameworks like Tailwind CSS in its current state.
```
