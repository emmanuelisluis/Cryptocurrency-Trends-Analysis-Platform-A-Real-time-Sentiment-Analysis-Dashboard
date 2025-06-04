"""
Application Configuration Management.

This module defines the application settings using Pydantic's BaseSettings,
allowing configuration via environment variables or a .env file.
"""
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Global application settings.
    Values are loaded from environment variables or a .env file.
    """
    # WebSocket URLs (Example, not currently used directly if hardcoded in client)
    # BINANCE_WS_BASE_URL: str = "wss://stream.binance.com:9443/ws"

    # Symbols to subscribe to for data ingestion
    SYMBOLS: List[str] = Field(default=["btcusdt", "ethusdt"], description="List of default symbols to subscribe to for data ingestion.")

    # Database URL
    DATABASE_URL: str = Field(default="postgresql://user:password@db:5432/crypto_dashboard", description="Database connection string.")
    # Note: The default DATABASE_URL points to the 'db' service name, typical in Docker Compose.
    # For local development outside Docker, this would be 'localhost' or actual DB host.

    # Order Book Imbalance Calculation Settings
    ORDER_BOOK_IMBALANCE_DEPTH_LEVELS: List[int] = Field(default=[5, 10, 20], description="Depth levels for order book imbalance calculation.")

    # Application settings
    APP_HOST: str = Field(default="0.0.0.0", description="Host for the FastAPI application.")
    APP_PORT: int = Field(default=8000, description="Port for the FastAPI application.")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level (e.g., DEBUG, INFO, WARNING, ERROR).")

    # ML Model Paths
    # These paths are relative to where the application is run.
    # In Docker, this would be relative to /app if WORKDIR is /app.
    MOMENTUM_SUSTAINABILITY_MODEL_PATH: Optional[str] = Field(
        default="backend/app/ml_models/momentum_model.pkl",
        description="Path to the momentum sustainability model file."
    )
    BREAKOUT_VIABILITY_MODEL_PATH: Optional[str] = Field(
        default="backend/app/ml_models/breakout_model.pkl",
        description="Path to the breakout viability model file."
    )
    ABSORPTION_OUTCOME_MODEL_PATH: Optional[str] = Field(
        default="backend/app/ml_models/absorption_model.pkl",
        description="Path to the absorption outcome model file."
    )

    # News API Configuration (CryptoCompare)
    CRYPTOCOMPARE_API_KEY: Optional[str] = Field(
        default="YOUR_CRYPTOCOMPARE_API_KEY_HERE",
        description="API key for CryptoCompare news API. User needs to replace this."
    )
    CRYPTOCOMPARE_NEWS_URL: str = Field(
        default="https://min-api.cryptocompare.com/data/v2/news/",
        description="Base URL for the CryptoCompare news API."
    )
    NEWS_CACHE_TTL_SECONDS: int = Field(
        default=60 * 10, # 10 minutes
        description="Time-to-live (TTL) in seconds for caching news articles."
    )

    # Pydantic-settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",              # Load from .env file
        env_file_encoding='utf-8',    # Encoding of .env file
        extra='ignore'                # Ignore extra fields not defined in the model
    )

# Create a single instance of the settings to be used throughout the application
settings = Settings()

# It's good practice to ensure __init__.py exists in the 'core' directory
# if it's treated as a package, but this file itself doesn't create other modules.
