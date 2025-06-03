from typing import Optional
from backend.app.services.data_ingestion_service import DataIngestionService
from backend.app.core.config import settings

# Global instance of DataIngestionService
# This instance will be initialized by the main application script (e.g., run_ingestion.py)
# and accessed by API endpoints.
data_ingestion_service_instance: Optional[DataIngestionService] = None

def initialize_global_data_ingestion_service():
    """Initializes the global data ingestion service instance."""
    global data_ingestion_service_instance
    if not settings.SYMBOLS:
        # This should ideally be handled by the calling script to log error and exit
        raise ValueError("Cannot initialize DataIngestionService: No symbols configured.")

    if data_ingestion_service_instance is None:
        data_ingestion_service_instance = DataIngestionService(symbols=settings.SYMBOLS)
    return data_ingestion_service_instance

def get_data_ingestion_service() -> DataIngestionService:
    """
    Returns the global instance of the DataIngestionService.
    Raises an exception if it's not initialized.
    """
    if data_ingestion_service_instance is None:
        # In a FastAPI context, this might happen if the endpoint is hit before service is ready.
        # Lifespan events are better for managing this. For now, direct check.
        raise RuntimeError("DataIngestionService has not been initialized.")
    return data_ingestion_service_instance

# Ensure __init__.py exists for the app directory (already created)
