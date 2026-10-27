"""
Unit tests for transaction CRUD, filtering, and validation.
Verifies requirements 1, 2, 3, 4, 5, 6, 13, 14.
"""

from datetime import date
from decimal import Decimal
import pytest
from pydantic import ValidationError
from schemas import TransactionCreate, TransactionUpdate
from services.transaction_service import (
    create_transaction,
    get_transaction_by_id,
    update_transaction,
    delete_transaction,
    list_transactions,
)


def test_successful_income_creation(db_session):
    """Verify requirement 1: Successful income creation."""
    payload = TransactionCreate(
        transaction_type="Income",
        amount=Decimal("15000.00"),
        category="Salary",
        transaction_date=date(2026, 10, 1),
        description="Monthly student stipend",
    )
    tx = create_transaction(payload, session=db_session)
    assert tx.id is not None
    assert tx.transaction_type == "Income"
    assert tx.amount == Decimal("15000.00")
    assert tx.category == "Salary"
    assert tx.description == "Monthly student stipend"


def test_successful_expense_creation(db_session):
    """Verify requirement 2: Successful expense creation."""
    payload = TransactionCreate(
        transaction_type="Expense",
        amount=Decimal("350.50"),
        category="Food",
        transaction_date=date(2026, 10, 5),
        description="Lunch at college cafeteria",
    )
    tx = create_transaction(payload, session=db_session)
    assert tx.id is not None
    assert tx.transaction_type == "Expense"
    assert tx.amount == Decimal("350.50")
    assert tx.category == "Food"


def test_rejection_of_zero_and_negative_amounts():
    """Verify requirement 3: Rejection of zero and negative amounts."""
    # Zero amount
    with pytest.raises(ValidationError):
        TransactionCreate(
            transaction_type="Expense",
            amount=Decimal("0.00"),
            category="Food",
            transaction_date=date(2026, 10, 5),
        )

    # Negative amount
    with pytest.raises(ValidationError):
        TransactionCreate(
            transaction_type="Expense",
            amount=Decimal("-100.00"),
            category="Food",
            transaction_date=date(2026, 10, 5),
        )

    # Negative amount in update
    with pytest.raises(ValidationError):
        TransactionUpdate(amount=Decimal("-50.00"))


def test_transaction_editing(db_session):
    """Verify requirement 4: Transaction editing."""
    tx = create_transaction(
        TransactionCreate(
            transaction_type="Expense",
            amount=Decimal("200.00"),
            category="Transportation",
            transaction_date=date(2026, 10, 10),
            description="Metro fare",
        ),
        session=db_session,
    )

    updated_tx = update_transaction(
        tx.id,
        TransactionUpdate(
            amount=Decimal("250.00"),
            description="Metro and bus fare",
        ),
        session=db_session,
    )
    assert updated_tx.amount == Decimal("250.00")
    assert updated_tx.description == "Metro and bus fare"
    assert updated_tx.category == "Transportation"


def test_transaction_deletion(db_session):
    """Verify requirement 5: Transaction deletion."""
    tx = create_transaction(
        TransactionCreate(
            transaction_type="Expense",
            amount=Decimal("500.00"),
            category="Shopping",
            transaction_date=date(2026, 10, 12),
        ),
        session=db_session,
    )
    deleted = delete_transaction(tx.id, session=db_session)
    assert deleted is True

    # Verify record is gone
    assert get_transaction_by_id(tx.id, session=db_session) is None


def test_handling_nonexistent_records(db_session):
    """Verify requirement 6: Handling nonexistent records."""
    assert get_transaction_by_id(99999, session=db_session) is None
    assert delete_transaction(99999, session=db_session) is False

    with pytest.raises(ValueError, match="not found"):
        update_transaction(99999, TransactionUpdate(amount=Decimal("100.00")), session=db_session)


def test_empty_database_handling(db_session):
    """Verify requirement 14: Empty database handling for transactions."""
    results = list_transactions(session=db_session)
    assert results == []


def test_transaction_filtering_and_sorting(db_session):
    """Verify requirement 13: Transaction filtering and sorting."""
    # Seed transactions
    create_transaction(
        TransactionCreate(
            transaction_type="Income",
            amount=Decimal("20000.00"),
            category="Allowance",
            transaction_date=date(2026, 10, 1),
            description="Parental allowance",
        ),
        session=db_session,
    )
    create_transaction(
        TransactionCreate(
            transaction_type="Expense",
            amount=Decimal("1500.00"),
            category="Food",
            transaction_date=date(2026, 10, 5),
            description="Grocery run",
        ),
        session=db_session,
    )
    create_transaction(
        TransactionCreate(
            transaction_type="Expense",
            amount=Decimal("800.00"),
            category="Books",
            transaction_date=date(2026, 10, 15),
            description="Python textbooks",
        ),
        session=db_session,
    )

    # 1. Filter by transaction type
    incomes = list_transactions(transaction_type="Income", session=db_session)
    assert len(incomes) == 1
    assert incomes[0].amount == Decimal("20000.00")

    # 2. Filter by category
    food_items = list_transactions(category="Food", session=db_session)
    assert len(food_items) == 1
    assert food_items[0].description == "Grocery run"

    # 3. Filter by date range
    range_items = list_transactions(
        start_date=date(2026, 10, 4),
        end_date=date(2026, 10, 10),
        session=db_session,
    )
    assert len(range_items) == 1
    assert range_items[0].category == "Food"

    # 4. Search description
    searched = list_transactions(search="textbooks", session=db_session)
    assert len(searched) == 1
    assert searched[0].category == "Books"

    # 5. Sorting by amount descending
    sorted_amt = list_transactions(sort_by="amount", sort_order="desc", session=db_session)
    assert sorted_amt[0].amount == Decimal("20000.00")
    assert sorted_amt[-1].amount == Decimal("800.00")
