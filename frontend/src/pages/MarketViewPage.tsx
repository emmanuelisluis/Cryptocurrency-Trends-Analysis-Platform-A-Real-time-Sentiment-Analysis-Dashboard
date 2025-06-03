import React from 'react';
import OrderBookDepthChart from '../components/market/OrderBookDepthChart';
import TimeAndSalesLog from '../components/market/TimeAndSalesLog';
import FootprintChart from '../components/market/FootprintChart'; // Import the new FootprintChart
import './MarketViewPage.css';

const MarketViewPage: React.FC = () => {
    const exchange = "binance";
    const symbol = "btcusdt";

    return (
        <div className="market-view-page">
            <header className="page-header">
                <h1>Market View: {symbol.toUpperCase()} on {exchange.toUpperCase()}</h1>
            </header>

            <div className="market-data-layout">
                {/* Top row for Order Book and Time & Sales */}
                <div className="market-data-row">
                    <section className="chart-section order-book-depth-section">
                        <h2>Order Book Depth & Imbalance</h2>
                        <OrderBookDepthChart exchange={exchange} symbol={symbol} pollInterval={5000} />
                    </section>

                    <section className="chart-section time-and-sales-section">
                        <h2>Time & Sales</h2>
                        <TimeAndSalesLog exchange={exchange} symbol={symbol} pollInterval={3000} />
                    </section>
                </div>

                {/* New row for Footprint Chart */}
                <div className="market-data-row">
                    <section className="chart-section footprint-chart-section">
                        <h2>Footprint Chart</h2>
                        <FootprintChart exchange={exchange} symbol={symbol} />
                    </section>
                </div>
            </div>

            {/* Other market data components could be added here */}
        </div>
    );
};

export default MarketViewPage;
