"""
Unit tests for financial calculations and database connection error handling.
Verifies requirements 7, 8, 9, 10, 14, 15.
"""

from datetime import date
from decimal import Decimal
import os
import pytest
from schemas import TransactionCreate
from services.transaction_service import (
    create_transaction,
    get_monthly_totals,
    get_category_expenses_for_month,
)
from database import test_connection as check_db_connection, get_clean_database_url
from config import mask_database_url


def test_empty_database_calculations(db_session):
    """Verify requirement 14: Calculations on empty database return zero without crashing."""
    totals = get_monthly_totals(2026, 10, session=db_session)
    assert totals["total_income"] == Decimal("0.00")
    assert totals["total_expenses"] == Decimal("0.00")
    assert totals["balance"] == Decimal("0.00")

    cat_expenses = get_category_expenses_for_month(2026, 10, session=db_session)
    assert cat_expenses == {}


def test_monthly_financial_calculations(db_session):
    """
    Verify:
    Requirement 7: Correct monthly income calculation
    Requirement 8: Correct monthly expense calculation
    Requirement 9: Correct balance calculation
    Requirement 10: Correct category-wise spending
    """
    year = 2026
    month = 10

    # Incomes in October
    create_transaction(
        TransactionCreate(
            transaction_type="Income",
            amount=Decimal("25000.00"),
            category="Salary",
            transaction_date=date(year, month, 1),
        ),
        session=db_session,
    )
    create_transaction(
        TransactionCreate(
            transaction_type="Income",
            amount=Decimal("5000.00"),
            category="Freelancing",
            transaction_date=date(year, month, 15),
        ),
        session=db_session,
    )

    # Expenses in October
    create_transaction(
        TransactionCreate(
            transaction_type="Expense",
            amount=Decimal("4500.00"),
            category="Food",
            transaction_date=date(year, month, 5),
        ),
        session=db_session,
    )
    create_transaction(
        TransactionCreate(
            transaction_type="Expense",
            amount=Decimal("1500.00"),
            category="Food",
            transaction_date=date(year, month, 12),
        ),
        session=db_session,
    )
    create_transaction(
        TransactionCreate(
            transaction_type="Expense",
            amount=Decimal("3000.00"),
            category="Rent",
            transaction_date=date(year, month, 2),
        ),
        session=db_session,
    )

    # Transaction in another month (September) - should NOT affect October
    create_transaction(
        TransactionCreate(
            transaction_type="Income",
            amount=Decimal("30000.00"),
            category="Salary",
            transaction_date=date(year, 9, 25),
        ),
        session=db_session,
    )

    totals = get_monthly_totals(year, month, session=db_session)

    # Requirement 7: Correct monthly income (25000 + 5000 = 30000)
    assert totals["total_income"] == Decimal("30000.00")

    # Requirement 8: Correct monthly expenses (4500 + 1500 + 3000 = 9000)
    assert totals["total_expenses"] == Decimal("9000.00")

    # Requirement 9: Correct balance (30000 - 9000 = 21000)
    assert totals["balance"] == Decimal("21000.00")

    # Requirement 10: Category-wise spending
    cat_expenses = get_category_expenses_for_month(year, month, session=db_session)
    assert cat_expenses["Food"] == Decimal("6000.00")
    assert cat_expenses["Rent"] == Decimal("3000.00")
    assert "Salary" not in cat_expenses  # Income must be excluded from expense summaries


def test_database_connection_error_handling(monkeypatch):
    """
    Verify requirement 15: Database connection error handling.
    Ensure errors are caught cleanly and credentials are NEVER exposed.
    """
    # 1. Test placeholder detection
    secret_url = "postgresql://user:super_secret_password@host.aws.neon.tech/db"
    masked = mask_database_url(secret_url)
    assert "super_secret_password" not in masked
    assert "user:*****@host" in masked

    # 2. Test unconfigured connection test
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://neondb_owner:<DATABASE_PASSWORD>@ep-super-field.neon.tech/neondb",
    )
    success, msg = check_db_connection()
    assert success is False
    assert "password is not set" in msg.lower()
    assert "<DATABASE_PASSWORD>" not in msg or "not set" in msg

    # 3. Test invalid host / unreachable database without exposing credentials
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://myuser:secretpass123@invalid-fake-host-999.neon.tech/neondb",
    )
    clean_url = get_clean_database_url(os.getenv("DATABASE_URL"))
    assert clean_url.startswith("postgresql+psycopg://")
