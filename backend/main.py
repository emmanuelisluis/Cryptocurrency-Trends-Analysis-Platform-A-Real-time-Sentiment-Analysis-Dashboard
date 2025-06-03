"""
Main FastAPI application for the Crypto Dashboard Backend.

This module initializes the FastAPI application, includes API routers,
and manages the lifecycle of background services like data ingestion.
"""
import asyncio
import logging

from fastapi import FastAPI

from backend.app.api.endpoints import market_data as market_data_router
from backend.app.api.endpoints import ml_predictions as ml_predictions_router
from backend.app.api.endpoints import status as status_router
from backend.app.globals import (
    data_ingestion_service_instance, # For direct access in shutdown
    get_data_ingestion_service,
    initialize_global_data_ingestion_service,
)
from backend.app.core.config import settings # To use LOG_LEVEL from settings

# Configure logging
# The basicConfig should ideally be called only once.
# If Uvicorn manages logging, this might be redundant or overridden.
# However, for standalone scripts or ensuring a default, it's often included.
# Using LOG_LEVEL from settings.
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# Create FastAPI app instance
app = FastAPI(
    title="Crypto Dashboard Backend",
    description="Provides APIs for market data, order flow analysis tools, and ML-driven predictions.",
    version="0.1.0" # Example version
)

# Include API routers
app.include_router(status_router.router, prefix="/api/v1", tags=["Status"])
app.include_router(market_data_router.router, prefix="/api/v1/market_data", tags=["Market Data"])
app.include_router(ml_predictions_router.router, prefix="/api/v1/ml", tags=["ML Predictions"])

# Lifespan events for managing background services like DataIngestionService
@app.on_event("startup")
async def startup_event():
    """
    Handles application startup events.
    Initializes and starts the DataIngestionService.
    """
    logger.info("FastAPI application startup sequence initiated...")
    try:
        logger.info("Initializing global DataIngestionService...")
        initialize_global_data_ingestion_service()
        service = get_data_ingestion_service()

        logger.info("Starting DataIngestionService as a background task...")
        # Store the task in app.state to manage it if needed, e.g., for graceful shutdown.
        app.state.data_ingestion_task = asyncio.create_task(service.start_ingestion())
        logger.info("DataIngestionService startup task created.")

    except Exception as e:
        logger.error(f"Critical error during DataIngestionService startup: {e}", exc_info=True)
        app.state.data_ingestion_task = None
        # Depending on the application's requirements, you might want to raise the exception
        # to prevent FastAPI from starting if data ingestion is absolutely critical.
        # For now, we log the error and the app will start, but ingestion might not work.

@app.on_event("shutdown")
async def shutdown_event():
    """
    Handles application shutdown events.
    Gracefully stops the DataIngestionService and cancels its background task.
    """
    logger.info("FastAPI application shutdown sequence initiated...")

    # Stop the DataIngestionService instance
    # data_ingestion_service_instance is imported from globals for direct access
    if data_ingestion_service_instance:
        logger.info("Attempting to stop DataIngestionService...")
        try:
            await data_ingestion_service_instance.stop_ingestion()
            logger.info("DataIngestionService stopped successfully.")
        except Exception as e:
            logger.error(f"Error occurred while stopping DataIngestionService: {e}", exc_info=True)
    else:
        logger.info("DataIngestionService instance not found, no service to stop.")

    # Cancel the background task if it was created and is still running
    ingestion_task = getattr(app.state, 'data_ingestion_task', None)
    if ingestion_task and not ingestion_task.done():
        logger.info("Cancelling DataIngestionService background task...")
        ingestion_task.cancel()
        try:
            await ingestion_task # Wait for the task to acknowledge cancellation
            logger.info("DataIngestionService background task was cancelled.")
        except asyncio.CancelledError:
            logger.info("DataIngestionService background task successfully processed cancellation.")
        except Exception as e:
            logger.error(f"Error during cancellation of DataIngestionService background task: {e}", exc_info=True)


@app.get("/", summary="Root Endpoint", description="Provides a welcome message and a link to the API documentation.")
async def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to Crypto Dashboard Backend API. Visit /docs for API documentation."}

# Note: This file defines the FastAPI application.
# It is typically run by an ASGI server like Uvicorn.
# Example command (from project root, if 'backend' is the package):
# uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
# The `run_ingestion.py` script in the project root handles this.
