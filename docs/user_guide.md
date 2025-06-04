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
    *   **Reading Depth:** Visualizes cumulative bid (typically green, growing from center to left) and ask (typically red, growing from center to right) volume. The Y-axis shows price levels, and the X-axis shows cumulative volume from the best bid/ask outwards. The chart helps identify areas of high liquidity (support/resistance).
    *   **Imbalance Stats:** Below the chart, this section shows the ratio of bid volume to total volume (bid + ask) at specific depths (e.g., top 5, 10, 20 levels from the Best Bid Offer - BBO). A ratio > 0.5 (or 50%) indicates more volume on the bid side at that depth; < 0.5 indicates more on the ask side.
    *   **OBDG Stats (Order Book Depth Gradient):** Compares volume in "near market" levels (e.g., first 5 levels) to "far market" levels (e.g., levels 6-20).
        *   `Bid Ratio (Near/Far)`: High ratio means more bid volume closer to market.
        *   `Ask Ratio (Near/Far)`: High ratio means more ask volume closer to market.
        *   `Overall Gradient Strength`: High ratio means more total volume (bids + asks) is concentrated near the market.
    *   *Polling:* The data for this chart updates automatically every few seconds.

*   **Time & Sales (Tape):**
    *   **Trade Log:** A chronological list of recent market trades. Columns typically include:
        *   `Time`: Timestamp of the trade.
        *   `Price`: Execution price.
        *   `Volume`: Quantity of the asset traded.
        *   `Side`: Indicates if the aggressor was a buyer (hitting an ask, usually green) or a seller (hitting a bid, usually red).
    *   **Filtering:**
        *   `Limit`: Adjusts the number of recent trades shown in the log.
        *   `Min Volume`: Filters the log to only show trades with volume greater than or equal to this value. Useful for spotting larger orders.
        *   `Large Vol Min`: Sets a threshold. Trades with volume meeting or exceeding this value will be visually highlighted in the log (e.g., made bold).
    *   *Polling:* Updates automatically every few seconds to show the latest trades.

*   **Footprint Chart:**
    *   **Reading Footprints:** Each candlestick (bar) is expanded to show trading volume at each price level within that bar. Inside each price level cell, you'll see `Bid Volume x Ask Volume`.
        *   `Bid Volume`: Volume resulting from sellers hitting bids (seller aggression).
        *   `Ask Volume`: Volume resulting from buyers hitting asks (buyer aggression).
    *   **Controls:**
        *   `Timeframe`: Select the bar interval (e.g., 1m, 5m, 1h). This is synchronized with the Global Timeframe selector.
        *   `Start/End Date/Time`: Use the date pickers to select the historical period for which to load footprint data.
        *   "Refresh Data": Manually re-fetches data for the selected parameters.
    *   **Visual Cues within each bar:**
        *   **Delta per Price:** Below the "Bid x Ask" text in each cell, a value in parentheses shows the delta for that price level (`Ask Volume - Bid Volume`). Positive delta (green text) means more aggressive buying; negative delta (red text) means more aggressive selling.
        *   **Total Bar Delta (Δ):** Displayed at the bottom (or top) of each bar, representing the sum of all price level deltas within that bar. Colored green for positive net delta, red for negative.
        *   **Point of Control (POC):** The price level within each bar that had the highest total volume. This cell is typically highlighted with a distinct border or background (e.g., gold).
        *   **Significant Imbalances:** Price level cells where aggressive buying significantly outweighs selling (e.g., Ask Volume is 3x Bid Volume) are highlighted with a strong green background. Conversely, cells with significant aggressive selling are highlighted with a strong red background.
        *   **Unfinished Auctions:** Cells at the extreme high or low of a bar might be highlighted (e.g., light orange for high, light blue for low) if conditions suggest the auction at that extreme was "unfinished" (e.g., bar closed near the high with strong ask imbalance at the high, indicating potential for further upward movement if buyers continue).
    *   **ML Predictions (Interactive):** See section 5 for details on how to trigger and interpret ML predictions by clicking on bars or price cells.

*   **Volume Profile Chart:**
    *   **Reading Profile:** Visualizes total volume traded at each price level over a specified period, displayed as horizontal bars. The Y-axis represents price, and the X-axis represents the total volume traded at that price.
    *   **Controls:**
        *   `Profile Type`:
            *   `DAILY`, `WEEKLY`, `MONTHLY`: Generates a profile for the selected day, week, or month. Use the "Date (UTC)" picker to select the reference date for the period.
            *   `RANGE`: Generates a profile for a custom date/time range. Use the "Start" and "End" datetime pickers.
        *   `Tick Size (Opt.)`: Optionally group prices by this increment. For example, if tick size is 0.5, prices like 100.1, 100.3, 100.4 would all be grouped into a level at 100.5 (if rounding to nearest tick) or 100.0. This can make profiles smoother for instruments with very small price steps.
        *   "Refresh Data": Manually re-fetches data.
    *   **Visual Cues:**
        *   **Point of Control (POC):** The price level with the highest traded volume within the selected period. This bar is typically highlighted (e.g., in gold/yellow).
        *   **Value Area (VA):** The range of prices where a significant percentage (typically 70%) of the total volume for the period was traded. Bars within the VA are usually colored differently (e.g., green) than those outside (e.g., grey).
        *   The chart also has reference lines marking the POC, VA High, and VA Low. A textual summary of these values is usually provided below the chart.

*   **CVD Chart (Cumulative Volume Delta):**
    *   **Interpreting CVD:** A line chart that shows the cumulative sum of bar deltas (Ask Volume - Bid Volume) over time. A rising CVD line indicates sustained net buying pressure, while a falling CVD line indicates sustained net selling pressure. Divergences between price action and CVD can be significant.
    *   **Controls:**
        *   `Timeframe (TF)`: Selects the timeframe of the underlying bars used to calculate the delta for each CVD point. This is synchronized with the Global Timeframe selector.
        *   `Reset`:
            *   `none`: CVD accumulates continuously over the entire selected date range.
            *   `daily`: CVD accumulation resets to 0 at the start of each new UTC day.
        *   `Start/End Date/Time`: Define the period for which to calculate and display CVD.
        *   "Refresh Data": Manually re-fetches data.
    *   **Divergence Drawing Tools:**
        *   "Draw Divergence" / "Cancel Drawing": A toggle button to enter or exit drawing mode.
        *   When drawing mode is active, click on two points on the CVD line to draw a straight line between them. This can be used to mark potential bullish or bearish divergences.
        *   "Clear Last Line": Removes the most recently drawn line.
        *   "Clear All Lines": Removes all user-drawn lines from the chart.

*   **Advanced Delta Metrics Chart (DVPR & DMRV):**
    *   **DVPR (Delta Volume Pressure Ratio):** Calculated as `Bar Delta / (Bar Volume * ATR)`. This metric normalizes delta by both volume and volatility (ATR). High positive values might indicate strong buying pressure that's significant relative to volume and volatility; high negative values indicate strong selling pressure. Values near zero might indicate balance or low conviction.
    *   **DMRV (Delta Moving Average Rate of Change/Value):** Calculated as `Short-term MA of Delta - Long-term MA of Delta`. This shows the momentum of delta. A positive DMRV indicates short-term delta momentum is stronger than long-term, suggesting increasing buying pressure. A negative DMRV suggests increasing selling pressure. Crossovers of the short and long MAs (where DMRV crosses zero) can also be points of interest.
    *   **Controls:**
        *   `Timeframe (TF)`: Selects the timeframe of the underlying bars. Synchronized with the Global Timeframe selector.
        *   `Start/End Date/Time`: Define the data range for calculation and display.
        *   `ATR P`: Sets the period for the Average True Range (ATR) calculation, which is used in DVPR.
        *   `DMRV Short/Long`: Sets the periods for the short-term and long-term Simple Moving Averages (SMAs) of delta used in DMRV calculation.
        *   "Refresh Data": Manually re-fetches data.
    *   **Charts:** DVPR and DMRV are displayed as separate line charts. The DMRV chart also plots the short-term and long-term delta MAs for context.

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

## 6. News & Sentiment Analysis Page
The dashboard includes a dedicated page for viewing cryptocurrency-related news and associated sentiment.

### Accessing the Page
*   Navigate to the "News & Sentiment" page using the link in the top global controls bar.

### Reading News
*   The page displays a list of recent news articles fetched from external sources (e.g., CryptoCompare).
*   Each news card typically shows:
    *   **Headline:** Clickable, linking to the original article.
    *   **Image:** If available.
    *   **Source:** The news provider (e.g., "Crypto News Today").
    *   **Date:** Publication date.
    *   **Summary:** A brief snippet of the article content.

### Interpreting Sentiment (Per Article)
*   Alongside each news article, a (currently simulated) sentiment analysis is displayed:
    *   **Label:** "Positive", "Negative", or "Neutral".
    *   **Score:** A numerical representation of the sentiment confidence (e.g., 0.0 to 1.0).
    *   **Indicator:** A colored dot (green for positive, red for negative, gray for neutral) provides a quick visual cue.
*   This sentiment is derived from the article's headline and/or summary.

## 7. Troubleshooting / FAQ (Placeholder)
*   **No Data Displayed:**
    *   Ensure correct exchange and symbol are selected.
    *   Check if the selected date range has trading activity for the chosen asset.
    *   Verify the backend data ingestion service is running and connected to the exchange.
*   **ML Predictions Not Working:**
    *   The ML models are currently simulated. They will provide placeholder predictions.
*   **Chart Performance:**
    *   Requesting very long date ranges with small timeframes (e.g., 1-minute footprints over many days) can be resource-intensive. Consider using appropriate ranges for the selected timeframe.
```
