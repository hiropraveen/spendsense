"""
Unit tests for budget management and utilization calculation.
Verifies requirements 11, 12, budget CRUD, and constraint handling.
"""

from datetime import date
from decimal import Decimal
import pytest
from pydantic import ValidationError
from schemas import BudgetCreate, BudgetUpdate, TransactionCreate
from services.transaction_service import create_transaction
from services.budget_service import (
    create_budget,
    get_budget_by_id,
    update_budget,
    delete_budget,
    get_budget_status_for_month,
    get_monthly_budget_summary,
)


def test_budget_creation_and_retrieval(db_session):
    """Verify successful budget creation."""
    payload = BudgetCreate(
        category="Food",
        amount=Decimal("5000.00"),
        budget_month=10,
        budget_year=2026,
    )
    b = create_budget(payload, session=db_session)
    assert b.id is not None
    assert b.category == "Food"
    assert b.amount == Decimal("5000.00")
    assert b.budget_month == 10
    assert b.budget_year == 2026

    retrieved = get_budget_by_id(b.id, session=db_session)
    assert retrieved is not None
    assert retrieved.category == "Food"


def test_budget_editing(db_session):
    """Verify budget amount updating."""
    b = create_budget(
        BudgetCreate(
            category="Transportation",
            amount=Decimal("2000.00"),
            budget_month=10,
            budget_year=2026,
        ),
        session=db_session,
    )
    updated = update_budget(b.id, BudgetUpdate(amount=Decimal("2500.00")), session=db_session)
    assert updated.amount == Decimal("2500.00")


def test_budget_deletion(db_session):
    """Verify budget deletion."""
    b = create_budget(
        BudgetCreate(
            category="Entertainment",
            amount=Decimal("1500.00"),
            budget_month=10,
            budget_year=2026,
        ),
        session=db_session,
    )
    assert delete_budget(b.id, session=db_session) is True
    assert get_budget_by_id(b.id, session=db_session) is None


def test_budget_duplicate_prevention(db_session):
    """Verify duplicate budgets for same category and month/year are prevented."""
    create_budget(
        BudgetCreate(
            category="Food",
            amount=Decimal("4000.00"),
            budget_month=10,
            budget_year=2026,
        ),
        session=db_session,
    )
    with pytest.raises(ValueError, match="already exists|Duplicate"):
        create_budget(
            BudgetCreate(
                category="Food",
                amount=Decimal("4500.00"),
                budget_month=10,
                budget_year=2026,
            ),
            session=db_session,
        )


def test_budget_rejection_of_invalid_values():
    """Verify rejection of invalid month or non-positive amount."""
    with pytest.raises(ValidationError):
        BudgetCreate(
            category="Food",
            amount=Decimal("0.00"),
            budget_month=10,
            budget_year=2026,
        )

    with pytest.raises(ValidationError):
        BudgetCreate(
            category="Food",
            amount=Decimal("1000.00"),
            budget_month=13,  # Invalid month
            budget_year=2026,
        )


def test_budget_utilization_and_warning_behavior(db_session):
    """
    Verify requirement 11 (correct budget utilization) and
    requirement 12 (budget warning behavior: NORMAL, WARNING, EXCEEDED).
    """
    year = 2026
    month = 10

    # 1. Budget under 80%: Normal (Budget ₹5000, Spend ₹2500 -> 50%)
    create_budget(
        BudgetCreate(
            category="Food",
            amount=Decimal("5000.00"),
            budget_month=month,
            budget_year=year,
        ),
        session=db_session,
    )
    create_transaction(
        TransactionCreate(
            transaction_type="Expense",
            amount=Decimal("2500.00"),
            category="Food",
            transaction_date=date(year, month, 5),
        ),
        session=db_session,
    )

    # 2. Budget between 80% and 100%: Warning (Budget ₹2000, Spend ₹1700 -> 85%)
    create_budget(
        BudgetCreate(
            category="Transportation",
            amount=Decimal("2000.00"),
            budget_month=month,
            budget_year=year,
        ),
        session=db_session,
    )
    create_transaction(
        TransactionCreate(
            transaction_type="Expense",
            amount=Decimal("1700.00"),
            category="Transportation",
            transaction_date=date(year, month, 8),
        ),
        session=db_session,
    )

    # 3. Budget over 100%: Exceeded (Budget ₹1000, Spend ₹1200 -> 120%)
    create_budget(
        BudgetCreate(
            category="Entertainment",
            amount=Decimal("1000.00"),
            budget_month=month,
            budget_year=year,
        ),
        session=db_session,
    )
    create_transaction(
        TransactionCreate(
            transaction_type="Expense",
            amount=Decimal("1200.00"),
            category="Entertainment",
            transaction_date=date(year, month, 12),
        ),
        session=db_session,
    )

    statuses = get_budget_status_for_month(year, month, session=db_session)
    status_map = {item["category"]: item for item in statuses}

    # Food: 50% -> NORMAL
    assert status_map["Food"]["utilization_pct"] == 50.0
    assert status_map["Food"]["status"] == "NORMAL"
    assert status_map["Food"]["remaining"] == Decimal("2500.00")

    # Transportation: 85% -> WARNING
    assert status_map["Transportation"]["utilization_pct"] == 85.0
    assert status_map["Transportation"]["status"] == "WARNING"
    assert status_map["Transportation"]["remaining"] == Decimal("300.00")

    # Entertainment: 120% -> EXCEEDED
    assert status_map["Entertainment"]["utilization_pct"] == 120.0
    assert status_map["Entertainment"]["status"] == "EXCEEDED"
    assert status_map["Entertainment"]["remaining"] == Decimal("-200.00")

    # Overall summary
    summary = get_monthly_budget_summary(year, month, session=db_session)
    assert summary["total_allocated_budget"] == Decimal("8000.00")
    # Total expenses = 2500 + 1700 + 1200 = 5400
    assert summary["total_expenses"] == Decimal("5400.00")
    # Overall utilization = (5400 / 8000) * 100 = 67.5%
    assert summary["budget_utilization_pct"] == 67.5
    assert summary["warning_count"] == 1
    assert summary["exceeded_count"] == 1
