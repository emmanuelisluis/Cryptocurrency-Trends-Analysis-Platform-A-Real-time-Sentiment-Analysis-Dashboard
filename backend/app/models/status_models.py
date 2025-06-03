from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class StreamStatus(BaseModel):
    stream_type: str             # e.g., "trade", "depth", "ticker"
    status: str                  # e.g., "connected", "connecting", "disconnected", "error", "stale", "stopped", "initializing"
    last_message_at: Optional[datetime] = None
    error_message: Optional[str] = None

class SymbolFeedStatus(BaseModel):
    symbol: str
    overall_symbol_status: str   # Overall status for this symbol's feeds (e.g. "connected", "degraded", "error")
    streams: List[StreamStatus]
    # error field was in the example, but stream-specific errors are in StreamStatus.
    # A symbol-level error could be for configuration issues, etc.
    # For now, let's rely on stream_errors and overall_symbol_status.
    # error: Optional[str] = None

class ExchangeClientStatus(BaseModel): # Renamed from ExchangeFeedStatus for clarity (it's client status)
    exchange_name: str
    client_connection_status: str # Overall status of the client itself (e.g. "connected", "error", "stopped")
    client_error_message: Optional[str] = None
    symbols: List[SymbolFeedStatus]

class DataFeedHealthResponse(BaseModel): # Top-level response model
    exchanges: List[ExchangeClientStatus]

# Ensure __init__.py exists for the models directory (already created)
