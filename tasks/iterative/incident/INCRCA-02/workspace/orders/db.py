"""
Database setup for the order system.
Uses SQLite in-memory database for testing.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from orders.models import Base

# Default to in-memory SQLite; override DATABASE_URL env var for other DBs
import os
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///:memory:?check_same_thread=False")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Return a new database session."""
    return SessionLocal()
