/**
 * GlobalControlsBar Component:
 * Provides UI elements for selecting the global market context, including
 * exchange, trading symbol, and analysis timeframe.
 * This component uses the GlobalMarketContext to access and update these global states.
 */
import React from 'react';
import { useGlobalMarket } from '../../contexts/GlobalMarketContext';
import './GlobalControlsBar.css';

// TODO: Replace MOCK_EXCHANGES and MOCK_SYMBOLS_BY_EXCHANGE with dynamic data.
// This could be fetched from a backend endpoint or a more robust configuration system.
/** Mock list of available exchanges. */
const MOCK_EXCHANGES = ['binance', 'coinbase_pro_simulated', 'kraken_simulated'];

/** Mock mapping of exchanges to their available trading symbols. */
const MOCK_SYMBOLS_BY_EXCHANGE: { [key: string]: string[] } = {
    binance: ['btcusdt', 'ethusdt', 'solusdt', 'dogeusdt', 'adausdt', 'xrpusdt'],
    coinbase_pro_simulated: ['btcusd', 'ethusd', 'solusd'],
    kraken_simulated: ['xbtusd', 'ethxbt', 'solxbt', 'adaxbt'], // Added one more for kraken
};

/** Mock list of available global timeframes. */
const MOCK_GLOBAL_TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '1d'];

/**
 * GlobalControlsBar functional component.
 * Renders dropdown selectors for exchange, symbol, and global timeframe.
 */
export const GlobalControlsBar: React.FC = () => {
    const {
        selectedExchange, setSelectedExchange,
        selectedSymbol, setSelectedSymbol,
        selectedGlobalTimeframe, setSelectedGlobalTimeframe
    } = useGlobalMarket();

    /**
     * Handles changes to the selected exchange.
     * Updates the global exchange and resets the symbol if the current symbol
     * is not available on the newly selected exchange.
     * @param event The change event from the exchange select element.
     */
    const handleExchangeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const newExchange = event.target.value;
        setSelectedExchange(newExchange);

        // Reset symbol if new exchange doesn't have the current one, or pick first available
        const symbolsForNewExchange = MOCK_SYMBOLS_BY_EXCHANGE[newExchange] || [];
        if (!symbolsForNewExchange.includes(selectedSymbol) || symbolsForNewExchange.length > 0) {
            setSelectedSymbol(symbolsForNewExchange[0] || '');
        }
    };

    /**
     * Handles changes to the selected symbol.
     * @param event The change event from the symbol select element.
     */
    const handleSymbolChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setSelectedSymbol(event.target.value);
    };

    /**
     * Handles changes to the selected global timeframe.
     * @param event The change event from the timeframe select element.
     */
    const handleTimeframeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setSelectedGlobalTimeframe(event.target.value);
    };

    // Determine available symbols for the currently selected exchange.
    const availableSymbols = MOCK_SYMBOLS_BY_EXCHANGE[selectedExchange] || [];

    return (
        <div className="global-controls-bar">
            {/* Exchange Selector */}
            <div className="control-group">
                <label htmlFor="exchange-select">Exchange:</label>
                <select
                    id="exchange-select"
                    value={selectedExchange}
                    onChange={handleExchangeChange}
                    aria-label="Select Exchange"
                >
                    {MOCK_EXCHANGES.map(ex => (
                        <option key={ex} value={ex}>
                            {/* Format exchange name for display (e.g., "coinbase_pro_simulated" to "Coinbase Pro Simulated") */}
                            {ex.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase())}
                        </option>
                    ))}
                </select>
            </div>

            {/* Symbol Selector */}
            <div className="control-group">
                <label htmlFor="symbol-select">Symbol:</label>
                <select
                    id="symbol-select"
                    value={selectedSymbol}
                    onChange={handleSymbolChange}
                    disabled={!availableSymbols.length}
                    aria-label="Select Symbol"
                >
                    {availableSymbols.map(sym => (
                        <option key={sym} value={sym}>
                            {sym.toUpperCase()}
                        </option>
                    ))}
                    {!availableSymbols.length && <option value="">N/A</option>}
                </select>
            </div>

            {/* Global Timeframe Selector */}
            <div className="control-group">
                <label htmlFor="global-timeframe-select">Timeframe:</label>
                <select
                    id="global-timeframe-select"
                    value={selectedGlobalTimeframe}
                    onChange={handleTimeframeChange} // Use dedicated handler
                    aria-label="Select Global Timeframe"
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
