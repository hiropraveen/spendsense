"""
Test configuration and fixtures for SpendSense.
Uses an isolated in-memory SQLite database to ensure tests never touch
the production Neon PostgreSQL database.
"""

import sys
from pathlib import Path

# Add project root to sys.path for test execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database import Base


@pytest.fixture(scope="function")
def db_session():
    """
    Creates an isolated in-memory SQLite database session for each test function.
    Tables are created fresh and dropped after each test.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
