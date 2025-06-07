"""Database session management for the Matching Service."""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session

from shared.config import get_config

# Get configuration
config = get_config()

# Create engine with connection pooling
engine = create_engine(
    config.get_database_uri(),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    echo=config.SQL_ECHO
)

# Create session factory
SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)


def get_db() -> Generator[Session, None, None]:
    """Get a database session.
    
    Yields:
        Database session that will be automatically closed
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database sessions.
    
    Usage:
        with get_db_context() as db:
            # perform database operations
            db.commit()
    
    Yields:
        Database session that will be automatically closed
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize the database.
    
    Creates all tables for the matching service schema.
    This is typically called during application startup.
    """
    # Import all models to ensure they're registered with SQLAlchemy
    from models import Platzsuche, Therapeutenanfrage, TherapeutAnfragePatient
    
    # Create all tables in the matching_service schema
    # Note: In production, use Alembic migrations instead
    from shared.utils.database import Base
    Base.metadata.create_all(bind=engine, checkfirst=True)


def close_db():
    """Close all database connections.
    
    This should be called when shutting down the application.
    """
    SessionLocal.remove()