import React from 'react';
import { useGlobalMarket } from '../../contexts/GlobalMarketContext';
import './GlobalControlsBar.css'; // Will create this CSS file next

// Mock data for available assets - ideally fetched or configured
// TODO: Replace with dynamic data, possibly fetched from backend or a more robust config
const MOCK_EXCHANGES = ['binance', 'coinbase_pro_simulated', 'kraken_simulated'];
const MOCK_SYMBOLS_BY_EXCHANGE: { [key: string]: string[] } = {
    binance: ['btcusdt', 'ethusdt', 'solusdt', 'dogeusdt', 'adausdt', 'xrpusdt'],
    coinbase_pro_simulated: ['btcusd', 'ethusd', 'solusd'],
    kraken_simulated: ['xbtusd', 'ethxbt', 'solxbt'],
};
// Mock data for timeframes - consistent with chart component options
const MOCK_GLOBAL_TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '1d'];


export const GlobalControlsBar: React.FC = () => {
    const {
        selectedExchange, setSelectedExchange,
        selectedSymbol, setSelectedSymbol,
        selectedGlobalTimeframe, setSelectedGlobalTimeframe // Added global timeframe
    } = useGlobalMarket();

    const handleExchangeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const newExchange = event.target.value;
        setSelectedExchange(newExchange);

        // Reset symbol if new exchange doesn't have the current one, or pick first available
        const symbolsForNewExchange = MOCK_SYMBOLS_BY_EXCHANGE[newExchange] || [];
        if (!symbolsForNewExchange.includes(selectedSymbol) || symbolsForNewExchange.length > 0) {
            setSelectedSymbol(symbolsForNewExchange[0] || ''); // Set to first symbol or empty if none
        }
    };

    const handleSymbolChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setSelectedSymbol(event.target.value);
    };

    const availableSymbols = MOCK_SYMBOLS_BY_EXCHANGE[selectedExchange] || [];

    return (
        <div className="global-controls-bar">
            <div className="control-group">
                <label htmlFor="exchange-select">Exchange:</label>
                <select id="exchange-select" value={selectedExchange} onChange={handleExchangeChange}>
                    {MOCK_EXCHANGES.map(ex => (
                        <option key={ex} value={ex}>
                            {ex.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} {/* Nicer display name */}
                        </option>
                    ))}
                </select>
            </div>
            <div className="control-group">
                <label htmlFor="symbol-select">Symbol:</label>
                <select
                    id="symbol-select"
                    value={selectedSymbol}
                    onChange={handleSymbolChange}
                    disabled={!availableSymbols.length}
                >
                    {availableSymbols.map(sym => (
                        <option key={sym} value={sym}>
                            {sym.toUpperCase()}
                        </option>
                    ))}
                    {!availableSymbols.length && <option value="">N/A</option>}
                </select>
            </div>
            {/* Timeframe selection will be added here in a subsequent subtask */}
            <div className="control-group">
                <label htmlFor="global-timeframe-select">Timeframe:</label>
                <select
                    id="global-timeframe-select"
                    value={selectedGlobalTimeframe}
                    onChange={(e) => setSelectedGlobalTimeframe(e.target.value)}
                >
                    {MOCK_GLOBAL_TIMEFRAMES.map(tf => (
                        <option key={tf} value={tf}>
                            {tf.toUpperCase()}
                        </option>
                    ))}
                </select>
            </div>
        </div>
    );
};
