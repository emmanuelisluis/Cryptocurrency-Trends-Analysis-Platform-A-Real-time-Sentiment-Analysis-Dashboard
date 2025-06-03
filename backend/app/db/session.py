"""
Database session management for SQLAlchemy.

This module sets up the SQLAlchemy engine and session factory.
It provides a dependency (`get_db`) for FastAPI to manage database sessions
per request, and a utility (`create_session`) for creating sessions
in other contexts (e.g., background tasks).
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session # Added Session for type hint
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

logger.info(f"Database URL: {settings.DATABASE_URL}") # Log DB URL on module load (be cautious in prod if URL has password)
# In a real app, you might want to mask the password if logging this.
# For now, assuming settings.DATABASE_URL might be a DSN that could be logged.

# Create a SQLAlchemy engine instance.
# `pool_pre_ping` checks connections for liveness before handing them out from the pool,
# which helps prevent issues with stale connections.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    # echo=True # Uncomment for debugging SQL queries, very verbose
)

# Create a SessionLocal factory to generate database sessions.
# These sessions are configured not to autocommit or autoflush, giving more control.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session: # Added return type hint
    """
    FastAPI dependency to get a database session per request.

    Yields:
        Session: The SQLAlchemy database session.

    Ensures the session is closed after the request is finished.
    """
    db: Optional[Session] = None # For type hinting
    try:
        db = SessionLocal()
        logger.debug(f"Database session {id(db)} opened.")
        yield db
    except Exception as e:
        logger.error(f"Error in database session {id(db)}: {e}", exc_info=True)
        # Depending on error handling strategy, you might rollback here
        # if db: db.rollback()
        raise # Re-raise the exception to be handled by FastAPI error handlers
    finally:
        if db:
            db.close()
            logger.debug(f"Database session {id(db)} closed.")

def create_session() -> Session:
    """
    Creates and returns a new SQLAlchemy session.
    Useful for background tasks or scripts that need to interact with the database
    outside of a FastAPI request lifecycle.

    Returns:
        Session: A new SQLAlchemy database session.

    The caller is responsible for closing this session.
    """
    try:
        session = SessionLocal()
        logger.debug(f"New standalone database session {id(session)} created.")
        return session
    except Exception as e:
        logger.error(f"Error creating standalone database session: {e}", exc_info=True)
        raise
