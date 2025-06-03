"""
Database Initialization Utility.

This module provides functions to initialize the database schema, including
creating standard tables based on SQLAlchemy models and converting relevant
tables into TimescaleDB hypertables.

It can be run as a script for initial setup:
`python -m backend.app.db.init_db`
"""
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text # For executing raw SQL

from backend.app.db.session import engine, create_session # Use create_session for explicit session management
from backend.app.db.models import Base # Import Base from SQLAlchemy models file
from backend.app.core.config import settings # For logging and DB URL check

logger = logging.getLogger(__name__)

# Define tables that should be converted to hypertables and their configurations
# Format: "table_name": {"time_column_name": "timestamp", "chunk_time_interval": "1 day"}
HYPERTABLE_CONFIG = {
    "trades": {"time_column_name": "timestamp", "chunk_time_interval": "1 day"},
    "tickers": {"time_column_name": "timestamp", "chunk_time_interval": "1 day"},
    "order_book_snapshots": {"time_column_name": "timestamp", "chunk_time_interval": "1 hour"},
}

def create_all_tables(engine_instance): # Pass engine explicitly
    """
    Creates all standard tables defined in SQLAlchemy models (via Base.metadata).
    It does not create hypertables.

    Args:
        engine_instance: The SQLAlchemy engine to bind to.
    """
    logger.info("Attempting to create all standard tables...")
    try:
        Base.metadata.create_all(bind=engine_instance)
        logger.info("Standard tables created successfully (if they didn't already exist).")
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError during table creation: {e}", exc_info=True)
        raise # Re-raise to indicate failure
    except Exception as e:
        logger.error(f"An unexpected error occurred during table creation: {e}", exc_info=True)
        raise # Re-raise

def create_hypertables(session): # Pass session explicitly
    """
    Converts specified tables into TimescaleDB hypertables.
    This function should be called after the standard tables have been created.

    Args:
        session: The SQLAlchemy session to use for executing commands.
    """
    logger.info(f"Attempting to create/verify hypertables for: {', '.join(HYPERTABLE_CONFIG.keys())}")
    for table_name, config in HYPERTABLE_CONFIG.items():
        time_column = config["time_column_name"]
        chunk_interval = config["chunk_time_interval"]

        # More robust check for hypertable existence first might be needed for older TimescaleDB versions
        # or if `create_hypertable` with `if_not_exists` is not perfectly idempotent in all scenarios.
        # For this project, `if_not_exists => TRUE` is relied upon.
        command = text(
            f"SELECT create_hypertable("
            f"'{table_name}', '{time_column}', "
            f"if_not_exists => TRUE, "
            f"chunk_time_interval => INTERVAL '{chunk_interval}'"
            f");"
        )
        try:
            session.execute(command)
            logger.info(f"Hypertable command executed for '{table_name}'. `if_not_exists` handles existing ones.")
        except SQLAlchemyError as e:
            # TimescaleDB might still raise an error if the table is already a hypertable
            # but with different parameters, or other specific conditions.
            # The `if_not_exists => TRUE` should prevent simple "already exists" errors.
            if "already a hypertable" in str(e).lower() or "already exists" in str(e).lower() or "multiple primary keys" in str(e).lower(): # Composite PKs are fine with Timescale
                logger.warning(
                    f"Could not create hypertable for '{table_name}' (it likely already exists or is configured): {e}"
                )
            else:
                logger.error(f"Error executing create_hypertable for '{table_name}': {e}", exc_info=True)
                # Optionally re-raise or collect errors to report overall failure
    try:
        session.commit() # Commit all hypertable creation commands
        logger.info("Hypertable creation/verification process completed.")
    except SQLAlchemyError as e:
        logger.error(f"Database error during commit of hypertable creation: {e}", exc_info=True)
        session.rollback()
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during commit of hypertable creation: {e}", exc_info=True)
        session.rollback()
        raise


def initialize_database():
    """
    Runs all database initialization steps:
    1. Creates standard tables.
    2. Creates/verifies TimescaleDB hypertables.
    """
    logger.info("Starting full database initialization process...")

    # Create standard tables
    create_all_tables(engine_instance=engine) # Use the global engine from session.py

    # Create/verify hypertables
    session = create_session() # Get a new session
    try:
        create_hypertables(session=session)
    finally:
        session.close() # Ensure session is closed

    logger.info("Database initialization process finished.")

if __name__ == "__main__":
    # Configure logging for direct script execution
    # Use LOG_LEVEL from settings for consistency.
    log_level_main = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level_main,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger.info("Running database initialization script directly...")

    # Check if DATABASE_URL is the default placeholder
    if "user:password@host:port/dbname" in settings.DATABASE_URL or \
       "user:password@db:5432/crypto_dashboard" in settings.DATABASE_URL: # Check against common placeholders
        logger.warning(
            f"DATABASE_URL ('{settings.DATABASE_URL}') seems to be a default placeholder. "
            "Ensure it's correctly configured in .env or environment variables before proceeding "
            "if you are targeting a specific production or development database."
        )
        # Example: prompt user to continue if desired
        # if input("Continue with this DATABASE_URL? (yes/no): ").lower() != 'yes':
        #     logger.info("Database initialization aborted by user.")
        #     exit(0)

    try:
        initialize_database()
        logger.info("Database initialization script completed successfully.")
    except Exception as e:
        logger.error(f"Database initialization script failed: {e}", exc_info=True)
        exit(1) # Exit with error code
