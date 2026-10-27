"""
SpendSense — Analytics Page
Interactive Plotly charts and financial intelligence:
1. Category Expense Doughnut Chart
2. Monthly Income vs Expense Comparison Bar Chart
3. Daily and Cumulative Spending Trend Chart
4. Budget vs Actual Comparison Chart
"""

from datetime import datetime
import streamlit as st
from config import APP_TITLE, CURRENCY_SYMBOL, format_currency
from ui_utils import (
    apply_custom_css,
    render_sidebar,
    render_page_header,
    render_metric_card,
    check_database_status,
)
from services.transaction_service import get_monthly_totals
from services.analytics_service import (
    build_expense_category_doughnut_chart,
    build_monthly_income_vs_expense_chart,
    build_daily_spending_trend_chart,
    build_budget_vs_actual_chart,
)

st.set_page_config(
    page_title=f"Analytics — {APP_TITLE}",
    page_icon="📈",
    layout="wide",
)

apply_custom_css()
render_sidebar()

render_page_header("📈 Financial Analytics & Trends", "Deep dive into your spending habits, income sources, and savings trends with Plotly charts.")

is_connected, db_msg = check_database_status()
if not is_connected:
    st.warning(f"⚠️ **Database Connection Required**\n\n{db_msg}")
    st.info("Configure your Neon database in the **⚙️ Settings** page to unlock full interactive analytics.")
    st.stop()

# Filter controls for period
now = datetime.now()
a_col1, a_col2, a_col3 = st.columns([2, 2, 2])

with a_col1:
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    sel_month_name = st.selectbox(
        "Analysis Month",
        options=month_names,
        index=now.month - 1,
        key="analytics_month",
    )
    sel_month = month_names.index(sel_month_name) + 1

with a_col2:
    years = list(range(now.year - 3, now.year + 2))
    sel_year = st.selectbox(
        "Analysis Year",
        options=years,
        index=years.index(now.year) if now.year in years else 0,
        key="analytics_year",
    )

with a_col3:
    history_months = st.selectbox(
        "History Horizon (for Monthly Comparison)",
        options=[3, 6, 12],
        index=1,
    )

st.write("")

# Key KPI summary
totals = get_monthly_totals(sel_year, sel_month)
savings_rate = 0.0
if totals["total_income"] > 0:
    savings_rate = float(round((totals["balance"] / totals["total_income"]) * 100, 1))

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
render_metric_card(kpi1, "Selected Month Income", format_currency(totals["total_income"]), f"{sel_month_name} {sel_year}", "income")
render_metric_card(kpi2, "Selected Month Expenses", format_currency(totals["total_expenses"]), f"{sel_month_name} {sel_year}", "expense")
render_metric_card(kpi3, "Net Savings", format_currency(totals["balance"]), "Retained cash", "balance" if totals["balance"] >= 0 else "expense")
render_metric_card(kpi4, "Savings Rate", f"{savings_rate:.1f}%", "% of income retained", "income" if savings_rate >= 20 else ("warning" if savings_rate >= 0 else "expense"))

st.write("")
st.markdown("---")

# Chart 1 & Chart 2
c_row1_left, c_row1_right = st.columns(2)

with c_row1_left:
    st.subheader("1. Expense Distribution by Category")
    st.caption("Doughnut breakdown of spending across all expense categories.")
    fig_doughnut = build_expense_category_doughnut_chart(sel_year, sel_month)
    st.plotly_chart(fig_doughnut, use_container_width=True)

with c_row1_right:
    st.subheader("2. Income vs Expense Comparison")
    st.caption(f"Historical cash inflow vs outflow across the past {history_months} months.")
    fig_bar = build_monthly_income_vs_expense_chart(months_count=history_months)
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# Chart 3 & Chart 4
c_row2_left, c_row2_right = st.columns(2)

with c_row2_left:
    st.subheader("3. Daily Spending Trend")
    st.caption(f"Burn rate & cumulative spending trajectory during {sel_month_name} {sel_year}.")
    fig_trend = build_daily_spending_trend_chart(sel_year, sel_month)
    st.plotly_chart(fig_trend, use_container_width=True)

with c_row2_right:
    st.subheader("4. Budget vs Actual Comparison")
    st.caption(f"Allocated limits compared against actual expenditure in {sel_month_name} {sel_year}.")
    fig_budget_vs_actual = build_budget_vs_actual_chart(sel_year, sel_month)
    st.plotly_chart(fig_budget_vs_actual, use_container_width=True)
