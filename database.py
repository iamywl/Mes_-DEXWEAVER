"""
Database configuration and session management for MES system.

This module configures the SQLAlchemy ORM connection to PostgreSQL
and provides database session management for the application.

Attributes:
    SQLALCHEMY_DATABASE_URL (str): PostgreSQL connection string.
    engine: SQLAlchemy engine instance.
    SessionLocal: SQLAlchemy session factory.
    Base: Declarative base for ORM models.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL configuration - can be overridden by environment variable
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234@postgres:5432/mes_db",
)

# Create engine with connection pooling
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create session factory with proper configuration
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Declarative base for ORM models
Base = declarative_base()


def get_db():
    """
    Database session dependency for FastAPI.

    Provides a database session for API route handlers.
    Automatically closes the session after request completion.

    Yields:
        Session: SQLAlchemy session instance.

    Example:
        @app.get("/items/")
        async def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

