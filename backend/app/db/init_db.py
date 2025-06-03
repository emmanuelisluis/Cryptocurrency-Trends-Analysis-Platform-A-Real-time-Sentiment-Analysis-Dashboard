import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

from backend.app.db.session import engine, SessionLocal
from backend.app.db.models import Base # Import Base from your models file

logger = logging.getLogger(__name__)

def create_all_tables():
    """
    Creates all tables defined in SQLAlchemy models.
    """
    try:
        logger.info("Attempting to create all tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully (if they didn't exist).")
    except SQLAlchemyError as e:
        logger.error(f"Error creating tables: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during table creation: {e}")
        raise

def create_hypertables():
    """
    Creates TimescaleDB hypertables for the specified tables.
    This needs to be executed after the tables themselves exist.
    """
    # Table names must match those defined in models.py
    hypertable_commands = [
        "SELECT create_hypertable('trades', 'timestamp', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 day');",
        "SELECT create_hypertable('tickers', 'timestamp', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 day');",
        "SELECT create_hypertable('order_book_snapshots', 'timestamp', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 hour');"
    ]

    session = SessionLocal()
    try:
        logger.info("Attempting to create hypertables...")
        for command in hypertable_commands:
            try:
                session.execute(text(command))
                logger.info(f"Successfully executed: {command.split('(')[1].split(',')[0]}") # Logs table name
            except SQLAlchemyError as e:
                # Handle specific case: if hypertable already exists, TimescaleDB might raise an error
                # depending on its version and `if_not_exists` behavior with `sqlalchemy-timescaledb`
                # The `if_not_exists => TRUE` should prevent errors, but good to be aware.
                if "already a hypertable" in str(e).lower() or "already exists" in str(e).lower() : # Crude check
                    logger.warning(f"Hypertable for command '{command}' likely already exists or another benign issue: {e}")
                else:
                    logger.error(f"Error creating hypertable with command '{command}': {e}")
                    # Optionally re-raise or collect errors
        session.commit()
        logger.info("Hypertable creation process completed.")
    except SQLAlchemyError as e:
        logger.error(f"Database error during hypertable creation: {e}")
        session.rollback()
        # raise # Optionally re-raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during hypertable creation: {e}")
        session.rollback()
        # raise # Optionally re-raise
    finally:
        session.close()

def initialize_database():
    """
    Runs all initialization steps: create tables, then create hypertables.
    """
    logger.info("Starting database initialization...")
    create_all_tables()
    create_hypertables()
    logger.info("Database initialization finished.")

if __name__ == "__main__":
    # This allows running `python -m backend.app.db.init_db` to initialize the database.
    # Ensure DATABASE_URL is correctly set in .env or environment variables.
    logging.basicConfig(level=logging.INFO)
    logger.info("Running database initialization script directly.")

    # Check if DATABASE_URL is configured
    from backend.app.core.config import settings
    if "user:password@host:port/dbname" in settings.DATABASE_URL: # Default placeholder
        logger.warning("DATABASE_URL is set to the default placeholder. Please configure it in .env.")
        # Decide if you want to exit or proceed with a potentially failing connection attempt
        # exit(1)

    initialize_database()
