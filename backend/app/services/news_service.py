import httpx
from typing import List, Optional, Dict # Ensure Dict is imported
from datetime import datetime, timedelta
import logging # Import logging

from app.core.config import settings
from app.models.news_models import NewsArticle, NewsApiResponse, NewsSourceInfo # Added NewsSourceInfo

logger = logging.getLogger(__name__) # Add logger

# Basic in-memory cache
_news_cache: Optional[List[NewsArticle]] = None
_news_cache_timestamp: Optional[datetime] = None

class NewsService:
    """
    Service for fetching crypto news articles from external APIs.
    """
    async def get_crypto_news(self, lang: str = "EN", categories: Optional[str] = None) -> List[NewsArticle]:
        """
        Fetches crypto news articles, using an in-memory cache.

        Args:
            lang: Language for the news (e.g., "EN").
            categories: Optional comma-separated string of categories to filter by (e.g., "BTC,ETH").

        Returns:
            A list of NewsArticle objects.
        """
        global _news_cache, _news_cache_timestamp

        # Check cache
        if _news_cache and _news_cache_timestamp and \
           (datetime.utcnow() - _news_cache_timestamp) < timedelta(seconds=settings.NEWS_CACHE_TTL_SECONDS):
            logger.info("Returning news from cache.")
            return _news_cache

        logger.info(f"Fetching fresh news. API Key: {'Set' if settings.CRYPTOCOMPARE_API_KEY and settings.CRYPTOCOMPARE_API_KEY != 'YOUR_CRYPTOCOMPARE_API_KEY_HERE' else 'Not Set (Using Placeholder - may fail)'}")

        headers = {}
        if settings.CRYPTOCOMPARE_API_KEY and settings.CRYPTOCOMPARE_API_KEY != "YOUR_CRYPTOCOMPARE_API_KEY_HERE":
            headers['authorization'] = f"Apikey {settings.CRYPTOCOMPARE_API_KEY}"

        params = {'lang': lang}
        if categories:
            params['categories'] = categories

        # If no API key, CryptoCompare might restrict or block.
        if not headers.get('authorization'):
            logger.warning("CryptoCompare API key is not set or is the placeholder. External API call might fail or be restricted.")
            # Fallback to dummy data if key is placeholder or missing
            return self._get_dummy_news_if_failed_or_empty(status_code=401) # Simulate auth failure

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(settings.CRYPTOCOMPARE_NEWS_URL, params=params, headers=headers)
                response.raise_for_status() # Raise an exception for bad status codes

                api_response_data = response.json()
                # Assuming the response structure matches NewsApiResponse directly or needs minor parsing
                parsed_response = NewsApiResponse(**api_response_data)

                if not parsed_response.Data: # If API returns success but no articles
                    logger.info("API returned success but no news articles. Returning dummy data.")
                    return self._get_dummy_news_if_failed_or_empty(status_code=response.status_code)

                _news_cache = parsed_response.Data
                _news_cache_timestamp = datetime.utcnow()
                logger.info(f"Fetched and cached {len(_news_cache)} news articles.")
                return _news_cache
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching news: {e.response.status_code} - {e.response.text}", exc_info=True)
            return self._get_dummy_news_if_failed_or_empty(e.response.status_code) # Return dummy on error
        except httpx.RequestError as e:
            logger.error(f"Request error fetching news: {e}", exc_info=True)
            return self._get_dummy_news_if_failed_or_empty() # Return dummy on error
        except Exception as e:
            logger.error(f"Unexpected error parsing news data: {e}", exc_info=True)
            # This might happen if the response structure is not what NewsApiResponse expects
            return self._get_dummy_news_if_failed_or_empty() # Return dummy on error

    def _get_dummy_news_if_failed_or_empty(self, status_code: Optional[int] = None) -> List[NewsArticle]:
        # Provide dummy data if API fails or returns empty, especially if no API key
        logger.warning(f"API call failed (status: {status_code}), was restricted, or returned no data. Returning dummy news articles.")
        dummy_articles = [
            NewsArticle(id="dummy1", guid="http://example.com/news1", published_on=datetime.utcnow() - timedelta(hours=1),
                        imageurl="https://via.placeholder.com/150/0000FF/808080?Text=News1", title="Major Bitcoin Rally Expected by Analysts",
                        url="http://example.com/news1", source="Crypto News Today", body="Detailed analysis suggests a major rally for Bitcoin as institutional interest grows and market indicators turn bullish.",
                        tags="Bitcoin,Rally,Analysis", categories="BTC,Market", lang="EN",
                        source_info=NewsSourceInfo(name="CNT", lang="EN", img="https://via.placeholder.com/50/0000FF/808080?Text=CNT")),
            NewsArticle(id="dummy2", guid="http://example.com/news2", published_on=datetime.utcnow() - timedelta(hours=2),
                        imageurl="https://via.placeholder.com/150/FF0000/FFFFFF?Text=News2", title="Ethereum Upgrade 'The Merge' Completes Successfully",
                        url="http://example.com/news2", source="ETH World", body="The much anticipated Ethereum upgrade, known as 'The Merge', has concluded, transitioning the network to Proof-of-Stake.",
                        tags="Ethereum,Merge,PoS", categories="ETH,Technology", lang="EN",
                        source_info=NewsSourceInfo(name="ETHW", lang="EN", img="https://via.placeholder.com/50/FF0000/FFFFFF?Text=ETHW")),
            NewsArticle(id="dummy3", guid="http://example.com/news3", published_on=datetime.utcnow() - timedelta(minutes=30),
                        imageurl="https://via.placeholder.com/150/008000/FFFFFF?Text=News3", title="New DeFi Protocol Launches with Record TVL",
                        url="http://example.com/news3", source="DeFi Times", body="A new decentralized finance protocol has launched today, attracting a record Total Value Locked (TVL) within hours of going live.",
                        tags="DeFi,TVL,NewProject", categories="DeFi", lang="EN",
                        source_info=NewsSourceInfo(name="DFT", lang="EN", img="https://via.placeholder.com/50/008000/FFFFFF?Text=DFT"))
        ]
        # Update cache with dummy data to prevent rapid retries on failing API
        global _news_cache, _news_cache_timestamp
        _news_cache = dummy_articles
        _news_cache_timestamp = datetime.utcnow() # Cache dummy data for the normal TTL
        return _news_cache
