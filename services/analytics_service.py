"""
Analytics service for SpendSense.
Generates Plotly interactive figures and data aggregates for financial insights.
"""

from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import select, and_, extract, func
from sqlalchemy.orm import Session
from database import get_db_session
from models import Transaction, Budget
from services.transaction_service import get_category_expenses_for_month
from services.budget_service import get_budget_status_for_month
from config import CURRENCY_SYMBOL

# Modern harmonious color palette
COLOR_INCOME = "#10B981"      # Emerald green
COLOR_EXPENSE = "#EF4444"     # Rose red
COLOR_BUDGET = "#6366F1"      # Indigo
COLOR_WARNING = "#F59E0B"     # Amber
COLOR_EXCEEDED = "#DC2626"    # Crimson red
CATEGORY_COLORS = [
    "#6366F1", "#EC4899", "#8B5CF6", "#10B981", "#F59E0B",
    "#3B82F6", "#14B8A6", "#F97316", "#06B6D4", "#84CC16",
]


def create_empty_figure(message: str = "No data available for the selected period.") -> go.Figure:
    """Return a styled blank figure with an empty state message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=15, color="#6B7280"),
    )
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=320,
        margin=dict(l=20, r=20, t=30, b=20),
    )
    return fig


def get_monthly_income_expense_history(
    months_count: int = 6,
    session: Optional[Session] = None,
) -> pd.DataFrame:
    """
    Fetch monthly income and expense history across the past N months.
    """
    def _fetch(s: Session) -> pd.DataFrame:
        stmt = (
            select(
                extract("year", Transaction.transaction_date).label("year"),
                extract("month", Transaction.transaction_date).label("month"),
                Transaction.transaction_type,
                func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            )
            .group_by("year", "month", Transaction.transaction_type)
            .order_by("year", "month")
        )
        rows = s.execute(stmt).all()
        if not rows:
            return pd.DataFrame(columns=["Period", "Income", "Expense"])

        data = {}
        for row in rows:
            yr = int(row[0])
            mo = int(row[1])
            ttype = row[2]
            amt = float(row[3])
            period_key = f"{yr}-{mo:02d}"

            if period_key not in data:
                data[period_key] = {"Period": period_key, "Income": 0.0, "Expense": 0.0}
            data[period_key][ttype] = amt

        # Sort and take last N months
        df = pd.DataFrame(list(data.values())).sort_values("Period")
        if len(df) > months_count:
            df = df.tail(months_count)
        return df

    if session:
        return _fetch(session)
    with get_db_session() as s:
        return _fetch(s)


def build_expense_category_doughnut_chart(
    year: int,
    month: int,
    session: Optional[Session] = None,
) -> go.Figure:
    """Build a donut chart showing expense distribution by category."""
    cat_expenses = get_category_expenses_for_month(year, month, session=session)
    if not cat_expenses or sum(cat_expenses.values()) <= Decimal("0.00"):
        return create_empty_figure("No expense records found for this month.")

    labels = list(cat_expenses.keys())
    values = [float(v) for v in cat_expenses.values()]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Amount: " + CURRENCY_SYMBOL + "%{value:,.2f}<br>Share: %{percent}<extra></extra>",
                marker=dict(colors=CATEGORY_COLORS),
            )
        ]
    )
    fig.update_layout(
        title=dict(text="<b>Expense Distribution by Category</b>", font=dict(size=16)),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=50, b=40),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def build_monthly_income_vs_expense_chart(
    months_count: int = 6,
    session: Optional[Session] = None,
) -> go.Figure:
    """Build a grouped bar chart comparing monthly income vs expenses."""
    df = get_monthly_income_expense_history(months_count=months_count, session=session)
    if df.empty or (df["Income"].sum() == 0 and df["Expense"].sum() == 0):
        return create_empty_figure("No monthly transaction history found.")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Income",
            x=df["Period"],
            y=df["Income"],
            marker_color=COLOR_INCOME,
            hovertemplate="Income: " + CURRENCY_SYMBOL + "%{y:,.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Expense",
            x=df["Period"],
            y=df["Expense"],
            marker_color=COLOR_EXPENSE,
            hovertemplate="Expense: " + CURRENCY_SYMBOL + "%{y:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text="<b>Monthly Income vs Expense</b>", font=dict(size=16)),
        barmode="group",
        xaxis_title="Month",
        yaxis_title=f"Amount ({CURRENCY_SYMBOL})",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=30, r=20, t=50, b=40),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#E5E7EB"),
    )
    return fig


def build_daily_spending_trend_chart(
    year: int,
    month: int,
    session: Optional[Session] = None,
) -> go.Figure:
    """Build a line chart illustrating cumulative and daily spending trends."""
    def _fetch(s: Session) -> pd.DataFrame:
        stmt = (
            select(
                Transaction.transaction_date,
                func.sum(Transaction.amount).label("daily_total"),
            )
            .where(
                and_(
                    extract("year", Transaction.transaction_date) == year,
                    extract("month", Transaction.transaction_date) == month,
                    Transaction.transaction_type == "Expense",
                )
            )
            .group_by(Transaction.transaction_date)
            .order_by(Transaction.transaction_date.asc())
        )
        rows = s.execute(stmt).all()
        if not rows:
            return pd.DataFrame(columns=["Date", "Daily", "Cumulative"])

        records = []
        cum = 0.0
        for r in rows:
            d_amt = float(r[1])
            cum += d_amt
            records.append({
                "Date": r[0].strftime("%b %d"),
                "Daily": d_amt,
                "Cumulative": cum,
            })
        return pd.DataFrame(records)

    if session:
        df = _fetch(session)
    else:
        with get_db_session() as s:
            df = _fetch(s)

    if df.empty:
        return create_empty_figure("No expense transactions recorded this month for trends.")

    fig = go.Figure()
    # Area chart for cumulative spending
    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Cumulative"],
            name="Cumulative Spend",
            mode="lines+markers",
            line=dict(color="#6366F1", width=3),
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.15)",
            hovertemplate="Cumulative: " + CURRENCY_SYMBOL + "%{y:,.2f}<extra></extra>",
        )
    )
    # Bar for daily spend
    fig.add_trace(
        go.Bar(
            x=df["Date"],
            y=df["Daily"],
            name="Daily Spend",
            marker_color="rgba(239, 68, 68, 0.6)",
            hovertemplate="Daily: " + CURRENCY_SYMBOL + "%{y:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text="<b>Daily & Cumulative Spending Trend</b>", font=dict(size=16)),
        xaxis_title="Day of Month",
        yaxis_title=f"Amount ({CURRENCY_SYMBOL})",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=30, r=20, t=50, b=40),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#E5E7EB"),
    )
    return fig


def build_budget_vs_actual_chart(
    year: int,
    month: int,
    session: Optional[Session] = None,
) -> go.Figure:
    """Build a grouped comparison chart of Budget vs Actual Spending."""
    statuses = get_budget_status_for_month(year, month, session=session)
    if not statuses:
        return create_empty_figure("No budgets set for this month. Create category budgets to view comparison.")

    categories = [s["category"] for s in statuses]
    budgets = [float(s["budget_amount"]) for s in statuses]
    actuals = [float(s["actual_spent"]) for s in statuses]
    colors = [
        COLOR_EXCEEDED if s["status"] == "EXCEEDED" else (COLOR_WARNING if s["status"] == "WARNING" else COLOR_EXPENSE)
        for s in statuses
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Allocated Budget",
            x=categories,
            y=budgets,
            marker_color=COLOR_BUDGET,
            hovertemplate="Budget: " + CURRENCY_SYMBOL + "%{y:,.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Actual Spent",
            x=categories,
            y=actuals,
            marker_color=colors,
            hovertemplate="Spent: " + CURRENCY_SYMBOL + "%{y:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text="<b>Budget vs Actual Spending by Category</b>", font=dict(size=16)),
        barmode="group",
        xaxis_title="Category",
        yaxis_title=f"Amount ({CURRENCY_SYMBOL})",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=30, r=20, t=50, b=40),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#E5E7EB"),
    )
    return fig
