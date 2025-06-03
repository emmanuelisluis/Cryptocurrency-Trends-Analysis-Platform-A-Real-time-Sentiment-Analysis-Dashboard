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
        Example: `REACT_APP_API_BASE_URL=/api/v1` (if frontend is served by the same domain as backend, or using a proxy)
        Or: `REACT_APP_API_BASE_URL=http://localhost:8000/api/v1` (if backend runs on a different port during development).
    *   Create `.env` by copying `.env.example` if provided, or manually. Standard `create-react-app` environment variable rules apply (must start with `REACT_APP_`).

## 2. Core Frontend Components

*   **`index.tsx`:** The entry point of the React application. Renders the `App` component into the DOM.
*   **`App.tsx` & Routing:**
    *   Main application shell component.
    *   Sets up `GlobalMarketProvider` for global state.
    *   Uses `react-router-dom` for client-side routing (e.g., defining paths to different pages like `MarketViewPage`).
    *   Includes basic layout like global navigation and footer.
*   **Contexts (`frontend/src/contexts/`):**
    *   `GlobalMarketContext.tsx`: Manages globally selected `exchange`, `symbol`, and `timeframe`. Provides these values and their setters to any component via the `useGlobalMarket` hook. This allows different components to react to a centralized market selection.
*   **Layout Components (`frontend/src/components/layout/`):**
    *   `GlobalControlsBar.tsx`: A bar displayed at the top of market views. Contains dropdowns for users to select the global exchange, symbol, and timeframe. Uses `GlobalMarketContext` to reflect and update these global selections.
*   **Pages (`frontend/src/pages/`):**
    *   `MarketViewPage.tsx`: The main page for displaying all market analysis charts and tools. It consumes `GlobalMarketContext` to get the current market selection and passes these (and the global timeframe) as props to the various chart components. It arranges these components in a responsive layout.
*   **Chart & Data Display Components (`frontend/src/components/market/`):** These are the primary analytical tools.
    *   `OrderBookDepthChart.tsx`:
        *   Displays order book depth using Recharts (Area chart).
        *   Shows aggregated imbalance statistics and Order Book Depth Gradient (OBDG) data.
        *   Polls the backend for updates.
    *   `TimeAndSalesLog.tsx`:
        *   Displays a chronological list of recent trades ("tape").
        *   Allows filtering by trade limit and minimum volume.
        *   Highlights large trades based on a user-configurable threshold.
        *   Polls for new trades.
    *   `FootprintChart.tsx`:
        *   Renders footprint charts using a custom Recharts configuration (BarChart with Customized cells).
        *   Displays bid volume vs. ask volume at each price level within bars.
        *   Highlights Delta, Point of Control (POC), significant imbalances, and potential unfinished auctions.
        *   Allows user to select timeframe and date range for data.
        *   Integrates ML prediction triggers:
            *   Clicking a bar can trigger Momentum Sustainability and Breakout Viability predictions.
            *   Clicking a price cell within a bar can trigger Absorption Outcome predictions.
        *   Displays ML prediction results in a dedicated section.
    *   `VolumeProfileChart.tsx`:
        *   Displays volume profile as a horizontal bar chart (Recharts `BarChart` with `layout="vertical"`).
        *   Shows total volume traded at each price level over a selected period/range.
        *   Highlights POC and Value Area (VA).
        *   Allows selection of profile type (daily, weekly, monthly, range) and relevant date/range parameters.
    *   `CVDChart.tsx` (Cumulative Volume Delta):
        *   Displays CVD as a line chart using Recharts.
        *   Allows selection of timeframe for underlying bar deltas, date range, and CVD reset condition (none, daily).
        *   Includes a feature for users to draw divergence lines directly on the chart.
    *   `AdvancedDeltaMetricsChart.tsx`:
        *   Displays DVPR (Delta Volume Pressure Ratio) and DMRV (Delta Moving Average Rate of Change/Value) in separate line charts using Recharts.
        *   Allows selection of timeframe, date range, and parameters for ATR and DMRV moving averages.
*   **API Service (`frontend/src/services/marketDataService.ts`):**
    *   Contains all functions responsible for making API calls to the backend.
    *   Uses the `fetch` API to interact with FastAPI endpoints.
    *   Defines TypeScript interfaces for API request parameters and response payloads, ensuring type safety.
    *   Includes functions for fetching order book data, trades, footprint data, volume profiles, CVD, advanced delta metrics, and for posting ML prediction requests.
*   **Styling:**
    *   Each major component typically has its own CSS file (e.g., `FootprintChart.css`).
    *   Global styles are in `App.css` and `index.css`.
    *   The approach is standard CSS, not CSS-in-JS or utility-first frameworks for this project phase.
```
