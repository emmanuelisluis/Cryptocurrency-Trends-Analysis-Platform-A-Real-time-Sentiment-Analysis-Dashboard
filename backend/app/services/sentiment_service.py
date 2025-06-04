import random
from typing import Dict # Ensure Dict is imported
import logging # Import logging

from app.models.sentiment_models import SentimentInput, SentimentOutput

logger = logging.getLogger(__name__) # Add logger

class SentimentService:
    """
    Service for performing sentiment analysis (currently simulated).
    """
    async def analyze_sentiment(self, input_data: SentimentInput) -> SentimentOutput:
        """
        Analyzes the sentiment of a given text.
        For V1, this returns a simulated sentiment.

        Args:
            input_data: SentimentInput object containing the text to analyze.

        Returns:
            A SentimentOutput object with the predicted sentiment.
        """
        logger.info(f"Simulating sentiment analysis for text: '{input_data.text[:50]}...'")

        # Simulate sentiment (randomly or based on simple rules)
        labels = ["positive", "negative", "neutral"]
        # Simple keyword-based heuristic (very basic)
        text_lower = input_data.text.lower()
        if any(word in text_lower for word in ["good", "great", "excellent", "rally", "bullish", "profit", "up", "gain", "positive", "buy", "long", "support", "breakout", "strong"]):
            simulated_label = "positive"
            simulated_score = random.uniform(0.6, 0.95)
        elif any(word in text_lower for word in ["bad", "poor", "terrible", "crash", "bearish", "loss", "down", "drop", "negative", "sell", "short", "resistance", "fakeout", "weak"]):
            simulated_label = "negative"
            simulated_score = random.uniform(0.6, 0.95)
        else:
            simulated_label = random.choice(labels)
            simulated_score = random.uniform(0.4, 0.7)

        # Ensure score is consistent with label if random choice was made
        if simulated_label == "positive" and simulated_score < 0.5:
            simulated_score = random.uniform(0.55, 0.95)
        elif simulated_label == "negative" and simulated_score < 0.5: # Assuming score is confidence in the label
            simulated_score = random.uniform(0.55, 0.95)
        elif simulated_label == "neutral" and (simulated_score > 0.65 or simulated_score < 0.35): # Neutral often lower confidence, tighten band
            simulated_score = random.uniform(0.4, 0.6)


        return SentimentOutput(
            text=input_data.text,
            sentiment_label=simulated_label,
            sentiment_score=round(simulated_score, 3),
            model_version="sim_keyword_v0.1.1" # Updated version
        )
