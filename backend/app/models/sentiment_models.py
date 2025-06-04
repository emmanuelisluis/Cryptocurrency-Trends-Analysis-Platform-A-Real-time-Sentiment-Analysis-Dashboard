from pydantic import BaseModel, Field, ConfigDict # Ensure ConfigDict is imported
from typing import Optional

class SentimentInput(BaseModel):
    text: str = Field(..., min_length=1, description="Text to be analyzed for sentiment.")
    # language: Optional[str] = Field("en", description="Language of the text (ISO 639-1 code). Currently informational for simulated version.")

class SentimentOutput(BaseModel):
    text: str = Field(description="The input text that was analyzed.")
    sentiment_label: str = Field(description="Predicted sentiment label (e.g., 'positive', 'negative', 'neutral').")
    sentiment_score: float = Field(description="Confidence score for the predicted label (e.g., 0.0 to 1.0). For simulated version, this might be a mock value.")
    # For multi-class probability:
    # probability_positive: Optional[float] = None
    # probability_negative: Optional[float] = None
    # probability_neutral: Optional[float] = None
    model_version: str = Field(default="sim_v0.1_sentiment", description="Version of the sentiment model used.")

    model_config = ConfigDict(from_attributes=True)
