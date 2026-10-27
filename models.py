"""
SQLAlchemy models for SpendSense expense tracker.
Defines tables for transactions and budgets.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    Text,
    DateTime,
    UniqueConstraint,
    Index,
    CheckConstraint,
)
from database import Base


def get_utc_now():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Transaction(Base):
    """
    Transactions table storing both Income and Expense records.
    Uses PostgreSQL NUMERIC for financial amounts to guarantee exact precision.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(String(10), nullable=False, index=True)  # 'Income' or 'Expense'
    amount = Column(Numeric(12, 2), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=get_utc_now,
        onupdate=get_utc_now,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('Income', 'Expense')",
            name="check_transaction_type_valid",
        ),
        CheckConstraint("amount > 0", name="check_transaction_amount_positive"),
        Index("ix_transactions_date_type", "transaction_date", "transaction_type"),
    )

    def __repr__(self):
        return f"<Transaction(id={self.id}, type='{self.transaction_type}', amount={self.amount}, category='{self.category}', date={self.transaction_date})>"


class Budget(Base):
    """
    Monthly category budgets table.
    Ensures unique budget per category per month and year.
    """
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    budget_month = Column(Integer, nullable=False)  # 1 to 12
    budget_year = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=get_utc_now,
        onupdate=get_utc_now,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "category",
            "budget_month",
            "budget_year",
            name="uq_budget_category_month_year",
        ),
        CheckConstraint(
            "budget_month >= 1 AND budget_month <= 12",
            name="check_budget_month_range",
        ),
        CheckConstraint("amount > 0", name="check_budget_amount_positive"),
        Index("ix_budgets_year_month", "budget_year", "budget_month"),
    )

    def __repr__(self):
        return f"<Budget(id={self.id}, category='{self.category}', amount={self.amount}, month={self.budget_month}, year={self.budget_year})>"
