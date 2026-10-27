"""
Database configuration and session management for SpendSense.
Integrates with Neon PostgreSQL via SQLAlchemy.
"""

import os
from contextlib import contextmanager
from typing import Generator, Tuple
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Load environment variables from .env
load_dotenv(override=True)

RAW_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def get_clean_database_url(url: str) -> str:
    """
    Format and validate database URL for SQLAlchemy.
    Normalizes postgresql:// to postgresql+psycopg:// if needed.
    """
    if not url:
        return ""
    # Strip quotes if present in .env
    url = url.strip('"').strip("'")
    if url.startswith("postgresql://"):
        # Use psycopg (psycopg 3) driver
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = get_clean_database_url(RAW_DATABASE_URL)

Base = declarative_base()

# Reusable singleton engine and sessionmaker
_engine = None
_SessionLocal = None


def get_engine():
    """Retrieve or initialize the singleton database engine."""
    global _engine
    if _engine is None:
        current_url = get_clean_database_url(os.getenv("DATABASE_URL", "").strip())
        if not current_url or "<DATABASE_PASSWORD>" in current_url:
            raise RuntimeError(
                "DATABASE_URL is missing or contains placeholder '<DATABASE_PASSWORD>'. "
                "Configure your Neon database password in the .env file."
            )
        _engine = create_engine(
            current_url,
            pool_pre_ping=True,
            pool_recycle=300,
        )
    return _engine


def get_sessionmaker():
    """Retrieve or initialize the singleton sessionmaker."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _SessionLocal


def reset_engine():
    """Reset engine if configuration changes dynamically."""
    global _engine, _SessionLocal
    if _engine:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Create a database session and always close it."""
    session_factory = get_sessionmaker()
    session: Session = session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> Tuple[bool, str]:
    """
    Test database connection using SELECT 1 without exposing credentials.
    Returns (True, message) on success, (False, error_message) on failure.
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if not url or "<DATABASE_PASSWORD>" in url:
        return (
            False,
            "Database password is not set in .env. Please configure your Neon connection string.",
        )
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Successfully connected to Neon PostgreSQL database."
    except Exception as e:
        # Sanitize any credentials in the error message
        err_msg = str(e)
        import re
        sanitized = re.sub(r":([^:@]+)@", r":*****@", err_msg)
        return False, f"Connection failed: {sanitized}"


def init_db():
    """
    Safely inspect the existing database and create tables if they do not exist.
    Never drops existing tables or deletes records.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine, checkfirst=True)
