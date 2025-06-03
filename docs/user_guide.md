# User Guide

This guide provides instructions on how to use the Crypto Dashboard.

## 1. Introduction
*   **Purpose:** The Crypto Dashboard is a tool for advanced market analysis, offering visualizations of order flow, volume profiles, and other delta-based metrics. It also integrates (simulated) ML predictions to provide insights into market dynamics.
*   **Key Features:**
    *   Real-time (via polling) Order Book Depth Chart with Imbalance and OBDG.
    *   Time & Sales log with large trade highlighting.
    *   Detailed Footprint Charts with bid/ask volume, delta, POC, imbalances, and unfinished auctions.
    *   Volume Profile visualization (daily, weekly, monthly, range) with POC and Value Area.
    *   Cumulative Volume Delta (CVD) chart with daily reset option and divergence drawing tools.
    *   Advanced Delta Metrics charts (DVPR, DMRV).
    *   Interactive ML predictions on Footprint Charts for Momentum Sustainability, Breakout Viability, and Absorption Outcome.
    *   Global controls for selecting exchange, symbol, and primary analysis timeframe.

## 2. Getting Started
*   **Accessing the Dashboard:** Open the deployed frontend URL in a web browser.
*   **Main Layout (`MarketViewPage`):**
    *   The primary view is the `MarketViewPage`.
    *   At the top, a `GlobalControlsBar` allows you to select the `Exchange`, `Symbol`, and `Timeframe` for analysis.
    *   Below this, various chart components are displayed, each focusing on different aspects of market data.

## 3. Global Controls
*   **Selecting Exchange and Symbol:**
    *   Use the "Exchange" dropdown in the `GlobalControlsBar` to choose the desired exchange (e.g., BINANCE).
    *   Once an exchange is selected, the "Symbol" dropdown will populate with available trading pairs for that exchange (e.g., BTCUSDT, ETHUSDT). Select your desired symbol.
    *   All charts on the page will update to reflect the selected exchange and symbol.
*   **Selecting Global Timeframe:**
    *   Use the "Timeframe" dropdown in the `GlobalControlsBar` (e.g., 1m, 5m, 1H).
    *   This global timeframe primarily affects charts that are bar-based and use this as their primary resolution, such as:
        *   Footprint Chart
        *   CVD Chart (uses this for its underlying bar delta calculation)
        *   Advanced Delta Metrics Chart (DVPR & DMRV)
    *   The Volume Profile chart might also adjust its default date range for "range" profiles based on this, but its core `profile_type` (daily, weekly) is selected within its own controls.
    *   Order Book and Time & Sales are not directly affected by this global timeframe selection as they show real-time or tick-level data.

## 4. Core Charts and Tools

*   **Order Book Depth Chart:**
    *   **Reading Depth:** Visualizes cumulative bid (green) and ask (red) volume at different price levels. The Y-axis shows price, X-axis shows cumulative volume.
    *   **Imbalance Stats:** Displays calculated bid/ask volume and imbalance ratios at configured depth levels (e.g., top 5, 10, 20 levels). A ratio > 50% indicates heavier bid-side volume at that depth.
    *   **OBDG Stats:** Shows Order Book Depth Gradient metrics, comparing volume distribution in "near market" vs. "far market" depth segments. Ratios indicate relative liquidity concentration.
    *   *Polling:* Updates every few seconds.

*   **Time & Sales (Tape):**
    *   **Trade Log:** A chronological list of recent trades. Columns: Time, Price, Volume, Side (Buy/Sell).
    *   **Filtering:**
        *   `Limit`: Control how many recent trades are displayed.
        *   `Min Volume`: Filter out trades smaller than this volume.
        *   `Large Vol Min`: Set a threshold to highlight "large" trades.
    *   **Large Trade Highlighting:** Trades exceeding the "Large Vol Min" threshold are visually emphasized (e.g., bold text).
    *   *Polling:* Updates every few seconds.

*   **Footprint Chart:**
    *   **Reading Footprints:** Each bar (candle) is broken down by price level. At each price, it shows `Bid Volume x Ask Volume` (volume traded by sellers hitting bids vs. volume traded by buyers hitting asks).
    *   **Controls:**
        *   `Timeframe`: Select the bar interval (e.g., 5m, 15m). Synchronized with global timeframe.
        *   `Start/End Date/Time`: Select the period for which to load footprint data.
        *   "Refresh Data" button.
    *   **Visual Cues:**
        *   **Delta per Price:** Text below "Bid x Ask" showing `(Ask Vol - Bid Vol)`, colored green for positive, red for negative.
        *   **Total Bar Delta:** Displayed at the bottom of each bar, colored by its sign.
        *   **Point of Control (POC):** Price level with the highest total volume within a bar, highlighted (e.g., gold border/fill).
        *   **Significant Imbalances:** Cells with strong bid/ask imbalance (e.g., 3x ratio) are highlighted with distinct backgrounds (e.g., strong green for ask imbalance, strong red for bid imbalance).
        *   **Unfinished Auctions:** Highlights at the bar's high/low if specific conditions (close proximity, strong counter-volume) suggest the auction might not have completed.
    *   **ML Predictions (Interactive):** See section 5.

*   **Volume Profile Chart:**
    *   **Reading Profile:** Displays total volume traded at each price level over a specified period, shown as horizontal bars. Y-axis is price, X-axis is total volume.
    *   **Controls:**
        *   `Profile Type`:
            *   `DAILY`, `WEEKLY`, `MONTHLY`: Uses the "Date (UTC)" selector to pick a reference date for the period.
            *   `RANGE`: Uses "Start" and "End" datetime pickers to define a custom range.
        *   `Tick Size (Opt.)`: Group prices by this increment for smoother profiles.
        *   "Refresh Data" button.
    *   **Visual Cues:**
        *   **Point of Control (POC):** Price level with the highest volume in the profile, highlighted (e.g., gold bar).
        *   **Value Area (VA):** Range of prices where a significant percentage (e.g., 70%) of the total volume was traded, highlighted with a different bar color (e.g., green).
        *   Reference lines and textual summary also indicate POC and VA range.

*   **CVD Chart (Cumulative Volume Delta):**
    *   **Interpreting CVD:** Shows the cumulative sum of bar deltas (Ask Volume - Bid Volume) over time as a line chart. Rising CVD indicates net buying pressure; falling CVD indicates net selling pressure.
    *   **Controls:**
        *   `Timeframe (TF)`: Timeframe of the underlying bars used for delta calculation. Synchronized with global timeframe.
        *   `Reset`:
            *   `none`: CVD accumulates continuously over the selected date range.
            *   `daily`: CVD resets to 0 at the start of each UTC day.
        *   `Start/End Date/Time`: Select the period for CVD calculation.
        *   "Refresh Data" button.
    *   **Divergence Drawing Tools:**
        *   "Draw Divergence" / "Cancel Drawing": Toggles drawing mode.
        *   When active, click two points on the CVD line to draw a line.
        *   "Clear Last Line" / "Clear All Lines": Manage drawn lines.

*   **Advanced Delta Metrics Chart (DVPR & DMRV):**
    *   **DVPR (Delta Volume Pressure Ratio):** `Bar Delta / (Bar Volume * ATR)`. Shows delta normalized by volume and volatility. Extreme values might indicate exhaustion or strong pressure.
    *   **DMRV (Delta Moving Average Rate of Change/Value):** `Short-term MA of Delta - Long-term MA of Delta`. Shows changes in delta momentum.
    *   **Controls:**
        *   `Timeframe (TF)`: Timeframe of underlying bars. Synchronized with global timeframe.
        *   `Start/End Date/Time`: Select the data range.
        *   `ATR P`: Period for ATR calculation (used in DVPR).
        *   `DMRV Short/Long`: Periods for the short-term and long-term moving averages of delta.
        *   "Refresh Data" button.
    *   **Charts:** DVPR and DMRV are displayed as separate line charts. The DMRV chart also shows the underlying short and long delta MAs.

## 5. ML Predictive Overlays (on Footprint Chart)
*   **Triggering Predictions:**
    *   **Momentum Sustainability & Breakout Viability:** Click directly on a footprint bar (the candle body or wick area).
    *   **Absorption Outcome:** Click on a specific price level cell (where "Bid x Ask" is shown) within a footprint bar.
*   **Inputting Custom Breakout Level:** For Breakout Viability, there's an input field below the prediction display areas where you can type a specific price. If a value is entered here, it will be used as the `breakout_price_level` when you next click a bar for a breakout prediction. If empty, the bar's close price is used by default.
*   **Momentum Sustainability Score:**
    *   Displayed after clicking a bar.
    *   **Score (0-10):** Higher score suggests the momentum indicated by the bar's delta is more likely to continue.
    *   **Confidence:** Model's confidence in this score (if provided).
*   **Breakout Viability Prediction:**
    *   Displayed after clicking a bar (uses bar's close as breakout level by default, or custom input).
    *   **P(True Breakout):** Probability the price will sustain movement beyond the `breakout_price_level`.
    *   **P(False Breakout):** Probability the price will fail to sustain beyond the level and potentially reverse.
*   **Absorption Event Outcome:**
    *   Displayed after clicking a specific price cell within a bar.
    *   **Predicted Label:** "Reversal", "Continuation", or "Consolidation" - the most likely outcome after the observed absorption at that price level.
    *   **Probabilities:** Shows the model's confidence for each of the three outcomes.
*   **Dismissing Predictions:** Each prediction box has a "Dismiss" button to clear it from view. New predictions replace old ones of the same type.

## 6. Troubleshooting / FAQ (Placeholder)
*   **No Data Displayed:**
    *   Ensure correct exchange and symbol are selected.
    *   Check if the selected date range has trading activity for the chosen asset.
    *   Verify the backend data ingestion service is running and connected to the exchange.
*   **ML Predictions Not Working:**
    *   The ML models are currently simulated. They will provide placeholder predictions.
*   **Chart Performance:**
    *   Requesting very long date ranges with small timeframes (e.g., 1-minute footprints over many days) can be resource-intensive. Consider using appropriate ranges for the selected timeframe.
```
