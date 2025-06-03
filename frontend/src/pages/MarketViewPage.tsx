import React from 'react';
import { useGlobalMarket } from '../../contexts/GlobalMarketContext'; // Import the hook
import { GlobalControlsBar } from '../../components/layout/GlobalControlsBar'; // Import the bar

import OrderBookDepthChart from '../components/market/OrderBookDepthChart';
import TimeAndSalesLog from '../components/market/TimeAndSalesLog';
import FootprintChart from '../components/market/FootprintChart';
import VolumeProfileChart from '../components/market/VolumeProfileChart';
import CVDChart from '../components/market/CVDChart';
import AdvancedDeltaMetricsChart from '../components/market/AdvancedDeltaMetricsChart';
import './MarketViewPage.css';

const MarketViewPage: React.FC = () => {
    const { selectedExchange, selectedSymbol, selectedGlobalTimeframe } = useGlobalMarket(); // Added selectedGlobalTimeframe

    // Key for re-rendering charts when global asset or timeframe changes.
    const chartKey = `${selectedExchange}-${selectedSymbol}-${selectedGlobalTimeframe}`;

    return (
        <div className="market-view-page">
            <GlobalControlsBar />

            <header className="page-header">
                <h1>
                    Market View: {selectedSymbol.toUpperCase()} on {selectedExchange.toUpperCase()}
                    {selectedGlobalTimeframe && ` (${selectedGlobalTimeframe.toUpperCase()})`} {/* Display global timeframe */}
                </h1>
            </header>

            {selectedExchange && selectedSymbol ? (
                <div className="market-data-layout">
                    {/* Top row for Order Book and Time & Sales (less affected by global timeframe directly) */}
                    <div className="market-data-row">
                        <section className="chart-section order-book-depth-section">
                            <h2>Order Book Depth & Imbalance</h2>
                            <OrderBookDepthChart key={`ob-${selectedExchange}-${selectedSymbol}`} exchange={selectedExchange} symbol={selectedSymbol} pollInterval={5000} />
                        </section>

                        <section className="chart-section time-and-sales-section">
                            <h2>Time & Sales</h2>
                            <TimeAndSalesLog key={`ts-${selectedExchange}-${selectedSymbol}`} exchange={selectedExchange} symbol={selectedSymbol} pollInterval={3000} />
                        </section>
                    </div>

                    {/* Chart sections that will use the global timeframe */}
                    <div className="market-data-row">
                        <section className="chart-section full-width-chart-section">
                            <h2>Footprint Chart</h2>
                            <FootprintChart key={`fp-${chartKey}`} exchange={selectedExchange} symbol={selectedSymbol} globalTimeframe={selectedGlobalTimeframe} />
                        </section>
                    </div>

                    <div className="market-data-row">
                        <section className="chart-section full-width-chart-section">
                            <h2>Volume Profile</h2>
                            {/* VolumeProfileChart might use globalTimeframe differently or for default range duration, not direct tf */}
                            <VolumeProfileChart key={`vp-${chartKey}`} exchange={selectedExchange} symbol={selectedSymbol} globalTimeframe={selectedGlobalTimeframe} />
                        </section>
                    </div>

                    <div className="market-data-row">
                        <section className="chart-section full-width-chart-section">
                            <h2>Cumulative Volume Delta (CVD)</h2>
                            <CVDChart key={`cvd-${chartKey}`} exchange={selectedExchange} symbol={selectedSymbol} globalTimeframe={selectedGlobalTimeframe} />
                        </section>
                    </div>

                    <div className="market-data-row">
                        <section className="chart-section full-width-chart-section">
                            <h2>Advanced Delta Metrics (DVPR & DMRV)</h2>
                            <AdvancedDeltaMetricsChart key={`adm-${chartKey}`} exchange={selectedExchange} symbol={selectedSymbol} globalTimeframe={selectedGlobalTimeframe} />
                        </section>
                    </div>
                </div>
            ) : (
                <div className="no-symbol-selected-message">
                    <p>Please select an exchange, symbol, and timeframe using the controls above.</p>
                </div>
            )}

        </div>
    );
};

export default MarketViewPage;
