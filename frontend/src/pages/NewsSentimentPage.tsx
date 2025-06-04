import React from 'react';
import { NewsDisplay } from '../components/news/NewsDisplay';
import './NewsSentimentPage.css'; // Create this CSS file

export const NewsSentimentPage: React.FC = () => {
    return (
        <div className="news-sentiment-page">
            <header className="page-header">
                <h1>News & Sentiment Analysis</h1>
            </header>
            <section className="news-section">
                <NewsDisplay />
            </section>
            <section className="sentiment-section">
                     {/* Sentiment components will be added here later, or this section can be repurposed for page-level sentiment summaries if needed. */}
            </section>
        </div>
    );
};
