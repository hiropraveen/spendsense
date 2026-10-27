"""
Configuration and constants for SpendSense - Smart Student Expense Tracker.
"""

from decimal import Decimal
from typing import Union
import re

APP_TITLE = "SpendSense"
APP_SUBTITLE = "Smart Student Expense Tracker"
CURRENCY_SYMBOL = "₹"

EXPENSE_CATEGORIES = [
    "Food",
    "Transportation",
    "Education",
    "Shopping",
    "Rent",
    "Bills",
    "Healthcare",
    "Entertainment",
    "Other",
]

INCOME_CATEGORIES = [
    "Salary",
    "Allowance",
    "Scholarship",
    "Freelancing",
    "Other",
]

CATEGORY_ICONS = {
    # Expense categories
    "Food": "🍔",
    "Transportation": "🚌",
    "Education": "📚",
    "Shopping": "🛍️",
    "Rent": "🏠",
    "Bills": "💡",
    "Healthcare": "🩺",
    "Entertainment": "🎬",
    # Income categories
    "Salary": "💼",
    "Allowance": "🎁",
    "Scholarship": "🎓",
    "Freelancing": "💻",
    # Fallback
    "Other": "🏷️",
}


def get_category_icon(category: str) -> str:
    """Return an icon representing the category."""
    return CATEGORY_ICONS.get(category, "🏷️")


def format_currency(amount: Union[Decimal, float, int, None]) -> str:
    """Format a monetary amount in Indian Rupees (₹) with comma grouping."""
    if amount is None:
        return f"{CURRENCY_SYMBOL}0.00"
    
    val = Decimal(str(amount))
    # Indian numbering format grouping or standard standard 2-decimal
    # e.g., ₹1,234.56
    sign = "-" if val < 0 else ""
    abs_val = abs(val)
    parts = f"{abs_val:,.2f}"
    return f"{sign}{CURRENCY_SYMBOL}{parts}"


def mask_database_url(url: str) -> str:
    """Mask credentials in database URL to prevent credential leakage."""
    if not url:
        return "[NOT CONFIGURED]"
    # Regex to mask password between : and @
    return re.sub(r":([^:@]+)@", r":*****@", url)
