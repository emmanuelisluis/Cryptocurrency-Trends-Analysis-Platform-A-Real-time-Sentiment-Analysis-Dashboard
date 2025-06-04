// frontend/src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { GlobalMarketProvider } from './contexts/GlobalMarketContext';
import { MarketViewPage } from './pages/MarketViewPage';
import { NewsSentimentPage } from './pages/NewsSentimentPage'; // Add this
import './App.css';

function App() {
  return (
    <GlobalMarketProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/market" element={<MarketViewPage />} />
            <Route path="/news-sentiment" element={<NewsSentimentPage />} /> {/* Add this route */}
            <Route path="/" element={<Navigate replace to="/market" />} />
          </Routes>
        </div>
      </Router>
    </GlobalMarketProvider>
  );
}

export default App;
