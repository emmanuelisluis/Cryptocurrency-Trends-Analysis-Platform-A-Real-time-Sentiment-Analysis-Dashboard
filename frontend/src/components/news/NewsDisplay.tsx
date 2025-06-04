import React, { useEffect, useState } from 'react';
import { NewsArticle, fetchCryptoNews, SentimentOutput, analyzeSentiment } from '../../services/marketDataService'; // Added SentimentOutput and analyzeSentiment
import './NewsDisplay.css';

// Define DisplayNewsArticle interface extending NewsArticle
interface DisplayNewsArticle extends NewsArticle {
    sentiment?: SentimentOutput | null;
    isSentimentLoading?: boolean;
    sentimentError?: string | null;
}

interface NewsDisplayProps {
    // Future props: categories, itemsPerPage, etc.
}

export const NewsDisplay: React.FC<NewsDisplayProps> = () => {
    const [displayArticles, setDisplayArticles] = useState<DisplayNewsArticle[]>([]); // Use DisplayNewsArticle
    const [isLoadingNews, setIsLoadingNews] = useState<boolean>(true); // Renamed for clarity
    const [newsError, setNewsError] = useState<string | null>(null); // Renamed for clarity

    useEffect(() => {
        const loadNewsAndSentiment = async () => {
            setIsLoadingNews(true);
            setNewsError(null);
            try {
                const articles = await fetchCryptoNews("EN", null);
                const articlesWithSentimentPlaceholders: DisplayNewsArticle[] = articles.map(article => ({
                    ...article,
                    sentiment: null,
                    isSentimentLoading: true,
                    sentimentError: null,
                }));
                setDisplayArticles(articlesWithSentimentPlaceholders);
                setIsLoadingNews(false);

                // Fetch sentiment for each article
                articlesWithSentimentPlaceholders.forEach(async (article, index) => {
                    // Analyze title, or a snippet of the body if title is too short or body exists
                    let textToAnalyze = article.title;
                    if (article.body && (article.title.length < 20 || article.body.length > article.title.length)) {
                        textToAnalyze = `${article.title}. ${article.body.substring(0, 250)}`; // Combine for more context
                    }

                    if (textToAnalyze && textToAnalyze.trim()) {
                        try {
                            const sentimentResult = await analyzeSentiment({ text: textToAnalyze });
                            setDisplayArticles(prevArticles => {
                                const newArticles = [...prevArticles];
                                if (newArticles[index]) {
                                    newArticles[index].sentiment = sentimentResult;
                                    newArticles[index].isSentimentLoading = false;
                                }
                                return newArticles;
                            });
                        } catch (sentimentErr: any) {
                            setDisplayArticles(prevArticles => {
                                const newArticles = [...prevArticles];
                                if (newArticles[index]) {
                                    newArticles[index].isSentimentLoading = false;
                                    newArticles[index].sentimentError = sentimentErr.message || 'Sentiment analysis failed.';
                                }
                                return newArticles;
                            });
                        }
                    } else {
                        setDisplayArticles(prevArticles => {
                            const newArticles = [...prevArticles];
                            if (newArticles[index]) {
                                newArticles[index].isSentimentLoading = false;
                                newArticles[index].sentimentError = "No text available for sentiment analysis.";
                            }
                            return newArticles;
                        });
                    }
                });

            } catch (err: any) {
                setNewsError(err.message || 'Failed to load news.');
                setDisplayArticles([]);
                setIsLoadingNews(false);
            }
        };
        loadNewsAndSentiment();
    }, []);

    if (isLoadingNews) return <p className="news-status">Loading news...</p>;
    if (newsError) return <p className="news-status news-error">Error loading news: {newsError}</p>;
    if (displayArticles.length === 0) return <p className="news-status">No news articles found.</p>;

    return (
        <div className="news-display-container">
            <h3>Latest Crypto News</h3>
            <div className="news-list">
                {displayArticles.map(article => (
                    <div key={article.id || article.guid} className="news-article-card">
                        {article.imageurl && (
                            <img src={article.imageurl} alt={article.title} className="news-article-image" />
                        )}
                        <div className="news-article-content">
                            <h4 className="news-article-title">
                                <a href={article.url} target="_blank" rel="noopener noreferrer">
                                    {article.title}
                                </a>
                            </h4>
                            <p className="news-article-meta">
                                <span className="news-article-source">{article.source_info.name}</span> |
                                <span className="news-article-date">{new Date(article.published_on).toLocaleDateString()}</span>
                            </p>
                            <p className="news-article-body">{article.body?.substring(0, 150)}{article.body && article.body.length > 150 ? '...' : ''}</p>

                            {/* Sentiment Display Section */}
                            <div className="news-article-sentiment">
                                {article.isSentimentLoading && <p className="sentiment-status">Loading sentiment...</p>}
                                {article.sentimentError && <p className="sentiment-status sentiment-error">Sentiment: {article.sentimentError}</p>}
                                {article.sentiment && !article.isSentimentLoading && (
                                    <p>
                                        <strong>Sentiment:</strong> {article.sentiment.sentiment_label}
                                        &nbsp;({article.sentiment.sentiment_score.toFixed(2)})
                                        <span className={`sentiment-indicator ${article.sentiment.sentiment_label.toLowerCase()}`}></span>
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
