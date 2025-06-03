from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # WebSocket URLs
    # BINANCE_WS_BASE_URL: str = "wss://stream.binance.com:9443/ws"

    # Symbols to subscribe to
    SYMBOLS: List[str] = ["btcusdt", "ethusdt"]

    # Database URL
    # The default value is for guidance; actual value should be in .env
    DATABASE_URL: str = "postgresql://user:password@host:port/dbname"

    # Order Book Imbalance Calculation Settings
    ORDER_BOOK_IMBALANCE_DEPTH_LEVELS: List[int] = [5, 10, 20] # Default levels to calculate imbalance for

    # Application settings
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"


    class Config:
        env_file = ".env"  # Specifies the .env file to load variables from
        env_file_encoding = 'utf-8'
        extra = 'ignore' # Ignore extra fields from .env not defined in Settings

settings = Settings()

# Ensure __init__.py exists for the core directory (already created)
