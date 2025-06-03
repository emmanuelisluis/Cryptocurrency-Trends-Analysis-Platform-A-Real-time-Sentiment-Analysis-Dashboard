import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import MarketViewPage from './pages/MarketViewPage';
import './App.css'; // Basic app-wide styles

function HomePage() {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>Welcome to Crypto Dashboard</h1>
      <p>Navigate to the Market View to see order book depth charts.</p>
      <nav>
        <Link to="/market">Go to Market View</Link>
      </nav>
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="App-nav">
          <ul>
            <li>
              <Link to="/">Home</Link>
            </li>
            <li>
              <Link to="/market">Market View</Link>
            </li>
            {/* Add other global navigation links here */}
          </ul>
        </nav>

        <main className="App-main-content">
          <Routes>
            <Route path="/market" element={<MarketViewPage />} />
            <Route path="/" element={<HomePage />} />
            {/* Define other routes here */}
          </Routes>
        </main>

        <footer className="App-footer">
          <p>&copy; {new Date().getFullYear()} Crypto Dashboard</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
