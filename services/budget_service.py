"""
Budget service for SpendSense.
Handles CRUD operations for monthly category budgets and calculates
actual spending, remaining amounts, and utilization percentages.
"""

from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, extract, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db_session
from models import Budget, Transaction
from schemas import BudgetCreate, BudgetUpdate


def create_budget(
    data: BudgetCreate,
    session: Optional[Session] = None,
) -> Budget:
    """
    Create a new budget for a category and month/year.
    Raises ValueError if a budget already exists for this category/month/year.
    """
    def _create(s: Session) -> Budget:
        # Check for existing budget
        existing = s.scalar(
            select(Budget).where(
                and_(
                    Budget.category == data.category,
                    Budget.budget_month == data.budget_month,
                    Budget.budget_year == data.budget_year,
                )
            )
        )
        if existing:
            raise ValueError(
                f"A budget for '{data.category}' in {data.budget_month:02d}/{data.budget_year} already exists. "
                "Please update the existing budget instead."
            )

        budget = Budget(
            category=data.category,
            amount=data.amount,
            budget_month=data.budget_month,
            budget_year=data.budget_year,
        )
        s.add(budget)
        try:
            s.commit()
            s.refresh(budget)
            return budget
        except IntegrityError as e:
            s.rollback()
            raise ValueError(
                f"Duplicate budget for '{data.category}' in {data.budget_month:02d}/{data.budget_year}."
            ) from e

    if session:
        return _create(session)
    with get_db_session() as s:
        return _create(s)


def get_budget_by_id(
    budget_id: int,
    session: Optional[Session] = None,
) -> Optional[Budget]:
    """Retrieve a budget by ID."""
    def _get(s: Session) -> Optional[Budget]:
        return s.get(Budget, budget_id)

    if session:
        return _get(session)
    with get_db_session() as s:
        return _get(s)


def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    session: Optional[Session] = None,
) -> Budget:
    """Update budget amount. Raises ValueError if not found."""
    def _update(s: Session) -> Budget:
        budget = s.get(Budget, budget_id)
        if not budget:
            raise ValueError(f"Budget with ID {budget_id} not found.")

        budget.amount = data.amount
        s.commit()
        s.refresh(budget)
        return budget

    if session:
        return _update(session)
    with get_db_session() as s:
        return _update(s)


def delete_budget(
    budget_id: int,
    session: Optional[Session] = None,
) -> bool:
    """Delete a budget by ID. Returns True if deleted, False if not found."""
    def _delete(s: Session) -> bool:
        budget = s.get(Budget, budget_id)
        if not budget:
            return False
        s.delete(budget)
        s.commit()
        return True

    if session:
        return _delete(session)
    with get_db_session() as s:
        return _delete(s)


def get_budgets_for_month(
    year: int,
    month: int,
    session: Optional[Session] = None,
) -> List[Budget]:
    """Get all configured category budgets for a specific month and year."""
    def _get(s: Session) -> List[Budget]:
        stmt = (
            select(Budget)
            .where(
                and_(
                    Budget.budget_year == year,
                    Budget.budget_month == month,
                )
            )
            .order_by(Budget.category.asc())
        )
        return list(s.scalars(stmt).all())

    if session:
        return _get(session)
    with get_db_session() as s:
        return _get(s)


def get_budget_status_for_month(
    year: int,
    month: int,
    session: Optional[Session] = None,
) -> List[Dict[str, Any]]:
    """
    Get detailed budget tracking for a month:
    Compares budgeted amount vs actual expense transactions.
    Calculates remaining amount, utilization percentage, and status:
    - 'EXCEEDED': > 100%
    - 'WARNING': >= 80% and <= 100%
    - 'NORMAL': < 80%
    """
    def _status(s: Session) -> List[Dict[str, Any]]:
        # 1. Fetch budgets for the month
        budgets = (
            s.scalars(
                select(Budget).where(
                    and_(
                        Budget.budget_year == year,
                        Budget.budget_month == month,
                    )
                )
            ).all()
        )

        # 2. Fetch actual expenses grouped by category
        exp_stmt = (
            select(
                Transaction.category,
                func.coalesce(func.sum(Transaction.amount), 0).label("spent"),
            )
            .where(
                and_(
                    extract("year", Transaction.transaction_date) == year,
                    extract("month", Transaction.transaction_date) == month,
                    Transaction.transaction_type == "Expense",
                )
            )
            .group_by(Transaction.category)
        )
        spent_by_category = {row[0]: Decimal(str(row[1])) for row in s.execute(exp_stmt).all()}

        results = []
        for b in budgets:
            budget_amt = Decimal(str(b.amount))
            actual_spent = spent_by_category.get(b.category, Decimal("0.00"))
            remaining = budget_amt - actual_spent

            if budget_amt > Decimal("0.00"):
                utilization_pct = float(round((actual_spent / budget_amt) * 100, 2))
            else:
                utilization_pct = 0.0

            if utilization_pct > 100.0:
                status = "EXCEEDED"
            elif utilization_pct >= 80.0:
                status = "WARNING"
            else:
                status = "NORMAL"

            results.append({
                "id": b.id,
                "category": b.category,
                "budget_amount": budget_amt,
                "actual_spent": actual_spent,
                "remaining": remaining,
                "utilization_pct": utilization_pct,
                "status": status,
                "budget_year": b.budget_year,
                "budget_month": b.budget_month,
            })

        return results

    if session:
        return _status(session)
    with get_db_session() as s:
        return _status(s)


def get_monthly_budget_summary(
    year: int,
    month: int,
    session: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Get aggregated monthly budget summary:
    - total_allocated_budget
    - total_budgeted_expenses (expenses in categories that have a budget)
    - total_expenses (all expenses in the month)
    - overall_utilization_pct
    - exceeded_count
    - warning_count
    """
    def _summary(s: Session) -> Dict[str, Any]:
        statuses = get_budget_status_for_month(year, month, session=s)
        total_budget = sum((item["budget_amount"] for item in statuses), Decimal("0.00"))
        
        # Total expenses for budgeted categories
        total_spent_budgeted = sum((item["actual_spent"] for item in statuses), Decimal("0.00"))

        # Total expenses overall for this month
        all_exp_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            and_(
                extract("year", Transaction.transaction_date) == year,
                extract("month", Transaction.transaction_date) == month,
                Transaction.transaction_type == "Expense",
            )
        )
        total_all_expenses = Decimal(str(s.scalar(all_exp_stmt) or 0))

        if total_budget > Decimal("0.00"):
            utilization_pct = float(round((total_all_expenses / total_budget) * 100, 2))
        else:
            utilization_pct = 0.0

        exceeded = [item for item in statuses if item["status"] == "EXCEEDED"]
        warning = [item for item in statuses if item["status"] == "WARNING"]

        return {
            "total_allocated_budget": total_budget,
            "total_spent_budgeted": total_spent_budgeted,
            "total_expenses": total_all_expenses,
            "budget_utilization_pct": utilization_pct,
            "exceeded_count": len(exceeded),
            "warning_count": len(warning),
            "budgets_count": len(statuses),
            "statuses": statuses,
        }

    if session:
        return _summary(session)
    with get_db_session() as s:
        return _summary(s)
