"""
Transaction service for SpendSense.
Handles all CRUD and financial summary operations on transactions.
Uses PostgreSQL NUMERIC and Python Decimal for accurate arithmetic.
"""

from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict
from sqlalchemy import select, and_, or_, func, desc, asc, extract
from sqlalchemy.orm import Session
from database import get_db_session
from models import Transaction
from schemas import TransactionCreate, TransactionUpdate


def create_transaction(
    data: TransactionCreate,
    session: Optional[Session] = None,
) -> Transaction:
    """Create a new income or expense transaction."""
    def _create(s: Session) -> Transaction:
        tx = Transaction(
            transaction_type=data.transaction_type,
            amount=data.amount,
            category=data.category,
            transaction_date=data.transaction_date,
            description=data.description.strip() if data.description else None,
        )
        s.add(tx)
        s.commit()
        s.refresh(tx)
        return tx

    if session:
        return _create(session)
    with get_db_session() as s:
        return _create(s)


def get_transaction_by_id(
    tx_id: int,
    session: Optional[Session] = None,
) -> Optional[Transaction]:
    """Retrieve a single transaction by ID."""
    def _get(s: Session) -> Optional[Transaction]:
        return s.get(Transaction, tx_id)

    if session:
        return _get(session)
    with get_db_session() as s:
        return _get(s)


def update_transaction(
    tx_id: int,
    data: TransactionUpdate,
    session: Optional[Session] = None,
) -> Transaction:
    """Update an existing transaction. Raises ValueError if not found."""
    def _update(s: Session) -> Transaction:
        tx = s.get(Transaction, tx_id)
        if not tx:
            raise ValueError(f"Transaction with ID {tx_id} not found.")

        if data.transaction_type is not None:
            tx.transaction_type = data.transaction_type
        if data.amount is not None:
            tx.amount = data.amount
        if data.category is not None:
            tx.category = data.category
        if data.transaction_date is not None:
            tx.transaction_date = data.transaction_date
        if data.description is not None:
            tx.description = data.description.strip() if data.description else None

        s.commit()
        s.refresh(tx)
        return tx

    if session:
        return _update(session)
    with get_db_session() as s:
        return _update(s)


def delete_transaction(
    tx_id: int,
    session: Optional[Session] = None,
) -> bool:
    """Delete a transaction by ID. Returns True if deleted, False if not found."""
    def _delete(s: Session) -> bool:
        tx = s.get(Transaction, tx_id)
        if not tx:
            return False
        s.delete(tx)
        s.commit()
        return True

    if session:
        return _delete(session)
    with get_db_session() as s:
        return _delete(s)


def list_transactions(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "date",  # 'date' or 'amount'
    sort_order: str = "desc",  # 'asc' or 'desc'
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    session: Optional[Session] = None,
) -> List[Transaction]:
    """
    Search and filter transactions with optional pagination and sorting.
    """
    def _list(s: Session) -> List[Transaction]:
        stmt = select(Transaction)
        conditions = []

        if start_date:
            conditions.append(Transaction.transaction_date >= start_date)
        if end_date:
            conditions.append(Transaction.transaction_date <= end_date)
        if category and category != "All":
            conditions.append(Transaction.category == category)
        if transaction_type and transaction_type != "All":
            conditions.append(Transaction.transaction_type == transaction_type)
        if search and search.strip():
            query_str = f"%{search.strip()}%"
            conditions.append(
                or_(
                    Transaction.description.ilike(query_str),
                    Transaction.category.ilike(query_str),
                )
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Sorting
        order_col = Transaction.transaction_date if sort_by == "date" else Transaction.amount
        if sort_order.lower() == "desc":
            stmt = stmt.order_by(desc(order_col), desc(Transaction.id))
        else:
            stmt = stmt.order_by(asc(order_col), asc(Transaction.id))

        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        return list(s.scalars(stmt).all())

    if session:
        return _list(session)
    with get_db_session() as s:
        return _list(s)


def get_monthly_totals(
    year: int,
    month: int,
    session: Optional[Session] = None,
) -> Dict[str, Decimal]:
    """
    Calculate monthly totals:
    - Total income = sum of income transactions in the selected period.
    - Total expenses = sum of expense transactions in the selected period.
    - Remaining balance = total income minus total expenses.
    """
    def _calc(s: Session) -> Dict[str, Decimal]:
        # Filter for the year and month
        # Use extract for cross-database compatibility (PostgreSQL & SQLite)
        base_cond = and_(
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
        )

        income_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            and_(base_cond, Transaction.transaction_type == "Income")
        )
        expense_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            and_(base_cond, Transaction.transaction_type == "Expense")
        )

        total_income = Decimal(str(s.scalar(income_stmt) or 0))
        total_expenses = Decimal(str(s.scalar(expense_stmt) or 0))
        remaining_balance = total_income - total_expenses

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": remaining_balance,
        }

    if session:
        return _calc(session)
    with get_db_session() as s:
        return _calc(s)


def get_category_expenses_for_month(
    year: int,
    month: int,
    session: Optional[Session] = None,
) -> Dict[str, Decimal]:
    """
    Calculate total expenses grouped by category for the specified month.
    """
    def _cat_expenses(s: Session) -> Dict[str, Decimal]:
        stmt = (
            select(
                Transaction.category,
                func.coalesce(func.sum(Transaction.amount), 0).label("total_spent"),
            )
            .where(
                and_(
                    extract("year", Transaction.transaction_date) == year,
                    extract("month", Transaction.transaction_date) == month,
                    Transaction.transaction_type == "Expense",
                )
            )
            .group_by(Transaction.category)
            .order_by(desc("total_spent"))
        )

        results = s.execute(stmt).all()
        return {row[0]: Decimal(str(row[1])) for row in results}

    if session:
        return _cat_expenses(session)
    with get_db_session() as s:
        return _cat_expenses(s)
