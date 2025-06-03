from fastapi import APIRouter, HTTPException, Depends
from typing import List

from backend.app.models.status_models import DataFeedHealthResponse, ExchangeClientStatus, SymbolFeedStatus, StreamStatus
from backend.app.globals import get_data_ingestion_service
from backend.app.services.data_ingestion_service import DataIngestionService

router = APIRouter()

# Dependency to get the service instance
# This ensures that if the service isn't initialized, endpoint returns an error.
# For a more robust solution, FastAPI's lifespan events would manage service initialization.
def get_service() -> DataIngestionService:
    try:
        return get_data_ingestion_service()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@router.get("/feed_health", response_model=DataFeedHealthResponse)
async def get_feed_health(
    service: DataIngestionService = Depends(get_service)
):
    """
    Retrieves the health status of all configured data feeds from exchanges.
    """
    try:
        clients_statuses_raw: List[Dict] = service.get_all_clients_status()

        # Transform raw status dictionaries into Pydantic models
        exchange_statuses: List[ExchangeClientStatus] = []
        for client_status_raw in clients_statuses_raw:
            symbol_feed_statuses: List[SymbolFeedStatus] = []
            for symbol_raw in client_status_raw.get("symbols", []):
                stream_statuses: List[StreamStatus] = []
                for stream_raw in symbol_raw.get("streams", []):
                    stream_statuses.append(StreamStatus(**stream_raw))

                symbol_feed_statuses.append(
                    SymbolFeedStatus(
                        symbol=symbol_raw.get("symbol"),
                        overall_symbol_status=symbol_raw.get("overall_symbol_status", "unknown"),
                        streams=stream_statuses
                    )
                )

            exchange_statuses.append(
                ExchangeClientStatus(
                    exchange_name=client_status_raw.get("exchange_name"),
                    client_connection_status=client_status_raw.get("client_connection_status", "unknown"),
                    client_error_message=client_status_raw.get("client_error_message"),
                    symbols=symbol_feed_statuses
                )
            )

        return DataFeedHealthResponse(exchanges=exchange_statuses)

    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching feed health: {str(e)}")

# Ensure __init__.py for endpoints (already created)
# Ensure __init__.py for api (already created)
