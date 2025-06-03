import asyncio
import logging
import signal # Keep signal for main process signal handling if needed, though uvicorn handles it for the app.
import uvicorn

from backend.app.core.config import settings
# The DataIngestionService and its instance are now managed via globals and FastAPI lifespan events
# from backend.app.services.data_ingestion_service import DataIngestionService
from backend.app.db.init_db import initialize_database
from backend.main import app # Import the FastAPI app

# Configure basic logging (this might be overridden by Uvicorn's log config)
# It's good to have a fallback if not run via Uvicorn directly or if Uvicorn doesn't manage all logs.
log_level_str = getattr(settings, 'LOG_LEVEL', 'INFO').upper()
numeric_log_level = getattr(logging, log_level_str, logging.INFO)

logging.basicConfig(
    level=numeric_log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
# Uvicorn's access logs can be noisy; its logger can be configured too if needed.
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)

# The DataIngestionService is now initialized and managed by FastAPI lifespan events in backend/main.py
# No need for global ingestion_service_instance here or run_data_ingestion async def.

def main():
    logger.info("Application startup sequence initiated from run_ingestion.py...")

    # --- Verify Database URL ---
    if "user:password@host:port/dbname" in settings.DATABASE_URL:
        logger.warning("DATABASE_URL is set to the default placeholder in config.py.")
        logger.warning("Please ensure a valid DATABASE_URL is provided via .env or environment variables for the application to work correctly.")
        # Depending on policy, you might want to exit if DB isn't properly configured.
        # For now, it will proceed, and DB operations will likely fail.
        # raise SystemExit("Exiting: DATABASE_URL is not configured properly.")

    # --- Database Initialization ---
    # This should be done before Uvicorn starts the app, as the app might need DB on startup.
    try:
        logger.info("Starting database initialization...")
        initialize_database()
        logger.info("Database initialization complete.")
    except Exception as e:
        logger.error(f"Critical error during database initialization: {e}", exc_info=True)
        logger.error("Application will not start without successful database initialization.")
        raise SystemExit(f"Exiting due to database initialization failure: {e}")

    # --- Symbol Configuration Check (optional here, as service init is in FastAPI) ---
    if not settings.SYMBOLS:
        logger.error("No symbols configured. Please set SYMBOLS in app/core/config.py or .env file.")
        # The DataIngestionService initialization (now in FastAPI lifespan) will also fail or warn.
        # raise SystemExit("Exiting: No symbols configured.")


    logger.info("Starting Uvicorn server for FastAPI application...")
    # Uvicorn will load the 'app' instance from 'backend.main'
    # Lifespan events in 'backend.main.py' will handle DataIngestionService start/stop.
    uvicorn.run(
        "backend.main:app",
        host=settings.APP_HOST if hasattr(settings, 'APP_HOST') else "0.0.0.0",
        port=settings.APP_PORT if hasattr(settings, 'APP_PORT') else 8000,
        log_level=log_level_str.lower(), # Uvicorn's own log level
        # reload=True # Enable reload for development, but typically not for this kind of script.
        # Consider adding reload_dirs=["backend"] if reload is True.
    )
    logger.info("Uvicorn server has shut down.")


if __name__ == "__main__":
    # The original signal handlers and asyncio event loop management are now largely handled by Uvicorn
    # and the FastAPI lifespan events. This script becomes a simple launcher.
    try:
        main()
    except SystemExit as e:
        logger.info(f"Application exited: {e}")
    except Exception as e: # Catch any other unexpected errors during main() execution
        logger.error(f"Unhandled exception in run_ingestion.py:main(): {e}", exc_info=True)
    finally:
        logger.info("run_ingestion.py finished.")
