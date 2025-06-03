"""
Pydantic models for representing the health status of data feeds and exchange clients.

These models are used by the status API endpoint to structure its response,
providing clients with an overview of the data ingestion pipeline's operational status.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class StreamStatus(BaseModel):
    """
    Represents the status of an individual data stream (e.g., trades for a specific symbol).
    """
    stream_type: str = Field(..., description="Type of the data stream (e.g., 'trade', 'depth', 'ticker').")
    status: str = Field(..., description="Current status of the stream (e.g., 'connected', 'connecting', 'disconnected', 'error', 'stale', 'stopped', 'initializing').")
    last_message_at: Optional[datetime] = Field(None, description="Timestamp of the last message received on this stream (UTC).")
    error_message: Optional[str] = Field(None, description="Any error message associated with this stream's current status.")

    model_config = ConfigDict(from_attributes=True)


class SymbolFeedStatus(BaseModel):
    """
    Aggregated status for all data streams related to a specific symbol on an exchange.
    """
    symbol: str = Field(..., description="Trading symbol (e.g., 'btcusdt').")
    overall_symbol_status: str = Field(..., description="Overall health status for this symbol's feeds (e.g., 'connected', 'degraded', 'error', 'stopped').")
    streams: List[StreamStatus] = Field(..., description="List of statuses for individual streams (trade, depth, ticker) for this symbol.")
    # error: Optional[str] = Field(None, description="Symbol-level error message, if any (e.g., configuration issues).") # Currently unused

    model_config = ConfigDict(from_attributes=True)


class ExchangeClientStatus(BaseModel):
    """
    Overall status of a connection to a specific exchange, including the status of all subscribed symbols.
    """
    exchange_name: str = Field(..., description="Name of the exchange (e.g., 'binance').")
    client_connection_status: str = Field(..., description="Overall connection status of the client for this exchange (e.g., 'connected', 'partially_connected', 'disconnected', 'error', 'stopped').")
    client_error_message: Optional[str] = Field(None, description="Any client-level error message for this exchange connection.")
    symbols: List[SymbolFeedStatus] = Field(..., description="Status of feeds for each subscribed symbol on this exchange.")

    model_config = ConfigDict(from_attributes=True)


class DataFeedHealthResponse(BaseModel):
    """
    Top-level API response model for data feed health status across all configured exchanges.
    """
    exchanges: List[ExchangeClientStatus] = Field(..., description="List of statuses for each connected exchange client.")

    model_config = ConfigDict(from_attributes=True)
