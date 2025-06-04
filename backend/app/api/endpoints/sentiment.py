from fastapi import APIRouter, Depends, HTTPException

from app.services.sentiment_service import SentimentService
from app.models.sentiment_models import SentimentInput, SentimentOutput

router = APIRouter()

@router.post("/analyze", response_model=SentimentOutput)
async def analyze_text_sentiment(
    input_data: SentimentInput,
    sentiment_service: SentimentService = Depends(SentimentService) # Dependency injection
):
    """
    Analyzes the sentiment of the provided text.

    Takes a JSON body with a "text" field.

    **Note:** This V1 implementation uses a *simulated* sentiment analysis model.
    It provides a basic heuristic or random sentiment for demonstration purposes and
    should not be used for production sentiment analysis.
    """
    if not input_data.text.strip(): # Check if text is empty or only whitespace
        raise HTTPException(status_code=400, detail="Input text cannot be empty or just whitespace.")
    try:
        result = await sentiment_service.analyze_sentiment(input_data)
        return result
    except HTTPException: # Re-raise HTTPExceptions if service layer were to raise them
        raise
    except Exception as e:
        # Ideally, specific exceptions from the service layer would be caught and handled.
        # For a general catch-all:
        # logger.error(f"Unexpected error during sentiment analysis: {e}", exc_info=True) # Requires logger
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during sentiment analysis: {str(e)}")
