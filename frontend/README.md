# Frontend

This directory contains the React/TypeScript frontend for the Crypto Dashboard.

It provides a user interface for:
- Selecting exchange, symbol, and global timeframe for analysis.
- Visualizing various market data charts:
    - Order Book Depth with Imbalance and OBDG statistics.
    - Time & Sales log with filtering and large trade highlighting.
    - Footprint Charts with detailed bid/ask volumes, delta, POC, imbalances, and unfinished auctions.
    - Volume Profile charts (daily, weekly, monthly, range) with POC and Value Area.
    - Cumulative Volume Delta (CVD) charts with reset options and divergence drawing tools.
    - Advanced Delta Metrics charts (DVPR, DMRV).
- Interacting with charts to trigger (simulated) ML predictions (Momentum Sustainability, Breakout Viability, Absorption Outcome) based on chart events.

## Core Technologies
- React (with Hooks and Functional Components)
- TypeScript
- Recharts (for charting)
- `react-router-dom` (for page navigation)
- `react-datepicker` (for date selection controls)
- Fetch API (for communicating with the backend)
- CSS (standard CSS files per component, no major framework)

For detailed setup instructions, architecture, and component descriptions, please see the [main frontend documentation here](../docs/frontend_setup.md).

To run the frontend:
1. Navigate to this `frontend` directory.
2. Install dependencies: `npm install` (or `yarn install`).
   *(Note: In some sandboxed development environments, installations for `recharts`, `react-datepicker`, and `react-router-dom` faced timeouts. These should install correctly in a standard local setup.)*
3. Ensure the backend server is running and accessible.
4. Configure your `.env` file if needed, especially `REACT_APP_API_BASE_URL` to point to your backend API (e.g., `REACT_APP_API_BASE_URL=http://localhost:8000/api/v1`).
5. Start the development server: `npm start` (or `yarn start`).

This will typically open the application in your default web browser at `http://localhost:3000`.
The main analytical tools are available on the "Market View" page.
