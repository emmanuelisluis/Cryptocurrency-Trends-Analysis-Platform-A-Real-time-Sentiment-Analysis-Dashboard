from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import settings

# Create a SQLAlchemy engine instance
# The pool_pre_ping checks connections for liveness before handing them out from the pool.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Create a SessionLocal factory to generate database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for FastAPI to get a DB session per request
# This is standard for FastAPI, but for background tasks like WebSocket ingestion,
# sessions will need to be created and managed explicitly.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create a new session, for use in background tasks or scripts
def create_session():
    return SessionLocal()
