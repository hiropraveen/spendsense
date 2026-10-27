"""
Pydantic schemas for data validation in SpendSense.
Validates transactions and budgets before database operations.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from config import EXPENSE_CATEGORIES, INCOME_CATEGORIES


class TransactionBase(BaseModel):
    transaction_type: str = Field(..., description="Income or Expense")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Amount must be greater than 0")
    category: str = Field(..., min_length=1, max_length=50)
    transaction_date: date = Field(..., description="Date of transaction")
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("transaction_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v_title = v.strip().capitalize()
        if v_title not in ["Income", "Expense"]:
            raise ValueError("Transaction type must be 'Income' or 'Expense'")
        return v_title

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str, info) -> str:
        category = v.strip()
        if not category:
            raise ValueError("Category cannot be empty")
        return category

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return round(v, 2)


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    transaction_type: Optional[str] = None
    amount: Optional[Decimal] = None
    category: Optional[str] = None
    transaction_date: Optional[date] = None
    description: Optional[str] = None

    @field_validator("transaction_type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_title = v.strip().capitalize()
        if v_title not in ["Income", "Expense"]:
            raise ValueError("Transaction type must be 'Income' or 'Expense'")
        return v_title

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v <= 0:
                raise ValueError("Amount must be greater than 0")
            return round(v, 2)
        return None


class TransactionRead(TransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BudgetBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=50)
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Monthly budget amount must be greater than 0")
    budget_month: int = Field(..., ge=1, le=12, description="Month from 1 to 12")
    budget_year: int = Field(..., ge=2000, le=2100, description="Valid year")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        cat = v.strip()
        if not cat:
            raise ValueError("Category cannot be empty")
        if cat not in EXPENSE_CATEGORIES:
            # We allow custom or standard expense categories
            pass
        return cat

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Budget amount must be greater than 0")
        return round(v, 2)


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Budget amount must be greater than 0")
        return round(v, 2)


class BudgetRead(BudgetBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
