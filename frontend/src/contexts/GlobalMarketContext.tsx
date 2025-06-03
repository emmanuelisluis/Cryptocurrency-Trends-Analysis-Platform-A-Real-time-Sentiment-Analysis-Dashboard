/**
 * React Context for managing global market selections (exchange, symbol, timeframe).
 * This allows various components across the application to access and potentially
 * modify the currently selected market context.
 */
import React, {
    createContext,
    useState,
    useContext,
    ReactNode,
    Dispatch,
    SetStateAction
} from 'react';

/**
 * Defines the shape of the global market state and its setter functions.
 */
export interface GlobalMarketState {
    /** Currently selected exchange identifier (e.g., "binance"). */
    selectedExchange: string;
    /** Function to update the selected exchange. */
    setSelectedExchange: Dispatch<SetStateAction<string>>;
    /** Currently selected trading symbol (e.g., "btcusdt"). */
    selectedSymbol: string;
    /** Function to update the selected trading symbol. */
    setSelectedSymbol: Dispatch<SetStateAction<string>>;
    /** Currently selected global timeframe (e.g., "5m", "1h"). */
    selectedGlobalTimeframe: string;
    /** Function to update the selected global timeframe. */
    setSelectedGlobalTimeframe: Dispatch<SetStateAction<string>>;
}

/**
 * React Context object for global market state.
 * Initialized with `undefined` and will throw an error if used outside its provider.
 */
const GlobalMarketContext = createContext<GlobalMarketState | undefined>(undefined);

/**
 * Props for the GlobalMarketProvider component.
 */
interface GlobalMarketProviderProps {
    children: ReactNode;
}

/**
 * Provider component that makes the global market state available to its children.
 * It initializes the default selected exchange, symbol, and timeframe.
 * @param {GlobalMarketProviderProps} props The props for the component.
 */
export const GlobalMarketProvider = ({ children }: GlobalMarketProviderProps) => {
    const [selectedExchange, setSelectedExchange] = useState<string>('binance');
    const [selectedSymbol, setSelectedSymbol] = useState<string>('btcusdt');
    const [selectedGlobalTimeframe, setSelectedGlobalTimeframe] = useState<string>('5m');

    // TODO: Consider fetching available exchanges and symbols from a backend endpoint
    // or a more robust configuration file in a real application.
    // const availableExchanges = ['binance', /* ... */];
    // const availableSymbolsByExchange = { binance: ['btcusdt', 'ethusdt', 'solusdt'], /* ... */ };

    return (
        <GlobalMarketContext.Provider value={{
            selectedExchange,
            setSelectedExchange,
            selectedSymbol,
            setSelectedSymbol,
            selectedGlobalTimeframe,
            setSelectedGlobalTimeframe
        }}>
            {children}
        </GlobalMarketContext.Provider>
    );
};

/**
 * Custom hook to easily access the GlobalMarketContext.
 * Throws an error if used outside of a GlobalMarketProvider, ensuring proper context usage.
 * @returns {GlobalMarketState} The current global market state and its setters.
 */
export const useGlobalMarket = (): GlobalMarketState => {
    const context = useContext(GlobalMarketContext);
    if (!context) {
        throw new Error('useGlobalMarket must be used within a GlobalMarketProvider. Ensure your component is wrapped by GlobalMarketProvider.');
    }
    return context;
};
