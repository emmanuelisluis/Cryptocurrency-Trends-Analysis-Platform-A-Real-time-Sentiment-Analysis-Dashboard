from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional

from app.services.news_service import NewsService
from app.models.news_models import NewsArticle

router = APIRouter()

@router.get("/crypto", response_model=List[NewsArticle])
async def get_crypto_news_endpoint(
    lang: str = Query("EN", description="Language for the news (e.g., EN, ES, JP). Default: EN"),
    categories: Optional[str] = Query(None, description="Comma-separated categories to filter news (e.g., BTC,ETH,DeFi). Check CryptoCompare API for available categories."),
    news_service: NewsService = Depends(NewsService) # Dependency injection for the service
):
    """
    Fetches the latest cryptocurrency news articles.

    Results are cached for a short period (e.g., 10 minutes) to reduce API load on the external provider.

    **Note:** This endpoint relies on the CryptoCompare API. A valid `CRYPTOCOMPARE_API_KEY`
    should be set in the backend's environment configuration for live data.
    If the API key is missing, invalid, or the external API call fails,
    **dummy data will be returned** to allow frontend development and basic functionality.
    """
    try:
        articles = await news_service.get_crypto_news(lang=lang, categories=categories)
        # The service now handles returning dummy data internally on failure or if no articles are found.
        # So, we typically expect 'articles' to be a list (possibly of dummy articles).
        # If the service were to return None or raise specific exceptions that we want to map to HTTP errors,
        # we could handle that here. For now, trust the service's fallback.
        if articles is None: # Should ideally not happen if service provides dummy data.
             # This case might indicate an unexpected issue in the service itself if it's supposed to always return a list.
             raise HTTPException(status_code=500, detail="News service returned an unexpected null response.")
        return articles
    except HTTPException: # Re-raise HTTPExceptions directly if service layer raises them (not current design)
        raise
    except Exception as e:
        # Log the exception details for debugging
        # logger.error(f"Unhandled error in news endpoint: {e}", exc_info=True) # Requires logger setup here
        # For now, rely on service-level logging.
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while fetching news: {str(e)}")
