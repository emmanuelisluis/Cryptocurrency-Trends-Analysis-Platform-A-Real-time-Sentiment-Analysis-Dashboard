import React, { createContext, useState, useContext, ReactNode, Dispatch, SetStateAction } from 'react';

interface GlobalMarketState {
    selectedExchange: string;
    setSelectedExchange: Dispatch<SetStateAction<string>>;
    selectedSymbol: string;
    setSelectedSymbol: Dispatch<SetStateAction<string>>;
    selectedGlobalTimeframe: string; // Added
    setSelectedGlobalTimeframe: Dispatch<SetStateAction<string>>; // Added
}

const GlobalMarketContext = createContext<GlobalMarketState | undefined>(undefined);

export const GlobalMarketProvider = ({ children }: { children: ReactNode }) => {
    const [selectedExchange, setSelectedExchange] = useState<string>('binance');
    const [selectedSymbol, setSelectedSymbol] = useState<string>('btcusdt');
    const [selectedGlobalTimeframe, setSelectedGlobalTimeframe] = useState<string>('5m'); // Default timeframe

    // Later: Add list of available exchanges/symbols, possibly fetched from backend
    // const availableExchanges = ['binance', /* ... */];
    // const availableSymbolsByExchange = { binance: ['btcusdt', 'ethusdt', 'solusdt'], /* ... */ };

    return (
        <GlobalMarketContext.Provider value={{
            selectedExchange, setSelectedExchange,
            selectedSymbol, setSelectedSymbol,
            selectedGlobalTimeframe, setSelectedGlobalTimeframe // Added to provider value
        }}>
            {children}
        </GlobalMarketContext.Provider>
    );
};

export const useGlobalMarket = (): GlobalMarketState => {
    const context = useContext(GlobalMarketContext);
    if (!context) {
        throw new Error('useGlobalMarket must be used within a GlobalMarketProvider');
    }
    return context;
};
