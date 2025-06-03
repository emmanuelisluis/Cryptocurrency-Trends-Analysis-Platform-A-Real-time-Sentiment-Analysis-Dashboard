from fastapi import FastAPI
from backend.app.api.endpoints import status as status_router
from backend.app.api.endpoints import market_data as market_data_router
from backend.app.api.endpoints import ml_predictions as ml_predictions_router # Added ML router import
from backend.app.globals import initialize_global_data_ingestion_service, get_data_ingestion_service, data_ingestion_service_instance
import asyncio
import logging

logger = logging.getLogger(__name__)
# Basic logging config, can be overridden by uvicorn's log config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# Create FastAPI app instance
app = FastAPI(title="Crypto Dashboard Backend")

# Include routers
app.include_router(status_router.router, prefix="/api/v1", tags=["Status"])
app.include_router(market_data_router.router, prefix="/api/v1/market_data", tags=["Market Data"])
app.include_router(ml_predictions_router.router, prefix="/api/v1/ml", tags=["ML Predictions"]) # Include ML router

# Lifespan events to manage DataIngestionService
@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application startup...")
    try:
        logger.info("Initializing DataIngestionService...")
        initialize_global_data_ingestion_service() # Creates the instance
        service = get_data_ingestion_service() # Retrieves it

        logger.info("Starting DataIngestionService in background...")
        # Running start_ingestion as a background task.
        # This task will run concurrently with the Uvicorn event loop.
        app.state.ingestion_task = asyncio.create_task(service.start_ingestion())
        logger.info("DataIngestionService startup task created and stored in app.state.")

    except Exception as e:
        logger.error(f"Error during DataIngestionService startup: {e}", exc_info=True)
        # Consider how to handle startup failure. If critical, app might need to exit.
        # For now, it logs. Health checks should report issues.
        app.state.ingestion_task = None # Ensure it's None if startup failed

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("FastAPI application shutdown...")

    # Stop the DataIngestionService
    if data_ingestion_service_instance: # Access global directly for shutdown safety
        logger.info("Stopping DataIngestionService...")
        try:
            await data_ingestion_service_instance.stop_ingestion()
            logger.info("DataIngestionService stopped.")
        except Exception as e:
            logger.error(f"Error stopping DataIngestionService: {e}", exc_info=True)
    else:
        logger.info("DataIngestionService instance not found, was it started?")

    # Cancel the background task if it exists and is running
    ingestion_task = getattr(app.state, 'ingestion_task', None)
    if ingestion_task and not ingestion_task.done():
        logger.info("Cancelling DataIngestionService background task...")
        ingestion_task.cancel()
        try:
            await ingestion_task # Wait for task to acknowledge cancellation
            logger.info("DataIngestionService background task cancelled.")
        except asyncio.CancelledError:
            logger.info("DataIngestionService background task successfully cancelled (as expected).")
        except Exception as e: # Should not happen if task handles cancellation gracefully
            logger.error(f"Error during background ingestion task cancellation: {e}", exc_info=True)


# Default route (optional)
@app.get("/")
async def read_root():
    return {"message": "Welcome to Crypto Dashboard Backend API. Visit /docs for API documentation."}

# This file defines the FastAPI application.
# To run it: uvicorn backend.main:app --reload (from /app directory)
# Or it will be run by run_ingestion.py as per subtask.
