"""
SpendSense — Dashboard Page
Displays monthly financial metrics, budget utilization, interactive charts, and recent activity.
"""

from datetime import datetime
import streamlit as st
import pandas as pd
from config import APP_TITLE, CURRENCY_SYMBOL, format_currency, get_category_icon
from ui_utils import (
    apply_custom_css,
    render_sidebar,
    render_page_header,
    render_metric_card,
    check_database_status,
)
from services.transaction_service import (
    get_monthly_totals,
    list_transactions,
)
from services.budget_service import get_monthly_budget_summary
from services.analytics_service import (
    build_expense_category_doughnut_chart,
    build_monthly_income_vs_expense_chart,
    build_daily_spending_trend_chart,
)

st.set_page_config(
    page_title=f"Dashboard — {APP_TITLE}",
    page_icon="📊",
    layout="wide",
)

apply_custom_css()
render_sidebar()

# Page header
render_page_header("📊 Dashboard", "High-level overview of student cashflow, budget health, and spending.")

# Verify DB connection
is_connected, db_msg = check_database_status()
if not is_connected:
    st.warning(
        f"⚠️ **Database Connection Required**\n\n{db_msg}\n\n"
        "Please configure your Neon PostgreSQL connection string in the `.env` file or in the **⚙️ Settings** page."
    )
    st.info("SpendSense connects directly to PostgreSQL on Neon. Once configured, your metrics and charts will appear here automatically.")
    st.stop()

# Date selector controls (Month & Year)
now = datetime.now()
col_m, col_y, col_refresh = st.columns([2, 2, 2])

with col_m:
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    selected_month_name = st.selectbox(
        "Select Month",
        options=month_names,
        index=now.month - 1,
        key="dash_month_select",
    )
    selected_month = month_names.index(selected_month_name) + 1

with col_y:
    years = list(range(now.year - 3, now.year + 2))
    selected_year = st.selectbox(
        "Select Year",
        options=years,
        index=years.index(now.year) if now.year in years else 0,
        key="dash_year_select",
    )

with col_refresh:
    st.write("")
    st.write("")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

st.write("")

# Retrieve monthly calculations
try:
    totals = get_monthly_totals(selected_year, selected_month)
    budget_summary = get_monthly_budget_summary(selected_year, selected_month)
except Exception as e:
    st.error(f"Error fetching data: {str(e)}")
    st.stop()

# Top 5 Financial Metric Cards
c1, c2, c3, c4, c5 = st.columns(5)

total_income = totals["total_income"]
total_expenses = totals["total_expenses"]
remaining_balance = totals["balance"]
total_budget = budget_summary["total_allocated_budget"]
utilization_pct = budget_summary["budget_utilization_pct"]

render_metric_card(
    c1,
    "Total Income",
    format_currency(total_income),
    f"{selected_month_name} {selected_year}",
    "income",
)
render_metric_card(
    c2,
    "Total Expenses",
    format_currency(total_expenses),
    f"{selected_month_name} {selected_year}",
    "expense",
)
render_metric_card(
    c3,
    "Remaining Balance",
    format_currency(remaining_balance),
    "Income − Expenses",
    "balance",
)
render_metric_card(
    c4,
    "Allocated Budget",
    format_currency(total_budget),
    f"{budget_summary['budgets_count']} categories budgeted",
    "budget",
)

# Utilization card styling
util_class = "income" if utilization_pct < 80 else ("warning" if utilization_pct <= 100 else "expense")
render_metric_card(
    c5,
    "Budget Utilization",
    f"{utilization_pct:.1f}%",
    f"Limit alerts: {budget_summary['exceeded_count']} exceeded",
    util_class,
)

# Budget warning alerts if any category exceeded
if budget_summary["exceeded_count"] > 0:
    exceeded_names = [
        f"**{item['category']}** ({format_currency(item['actual_spent'])} / {format_currency(item['budget_amount'])})"
        for item in budget_summary["statuses"]
        if item["status"] == "EXCEEDED"
    ]
    st.error(
        f"🚨 **Budget Alert**: {budget_summary['exceeded_count']} category budget(s) have been exceeded this month: "
        + ", ".join(exceeded_names)
        + ". Check the **Budgets** page to adjust limits or rein in spending."
    )
elif budget_summary["warning_count"] > 0:
    warning_names = [
        f"**{item['category']}** ({item['utilization_pct']:.0f}%)"
        for item in budget_summary["statuses"]
        if item["status"] == "WARNING"
    ]
    st.warning(
        f"⚠️ **Budget Warning**: {budget_summary['warning_count']} category budget(s) are near their limit (≥80%): "
        + ", ".join(warning_names)
    )

st.write("")

# Interactive Charts
st.subheader("📈 Financial Analytics")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    fig_donut = build_expense_category_doughnut_chart(selected_year, selected_month)
    st.plotly_chart(fig_donut, use_container_width=True)

with chart_col2:
    fig_bar = build_monthly_income_vs_expense_chart(months_count=6)
    st.plotly_chart(fig_bar, use_container_width=True)

# Spending Trend
st.plotly_chart(
    build_daily_spending_trend_chart(selected_year, selected_month),
    use_container_width=True,
)

st.write("")
st.subheader("🕒 Recent Transactions")

recent_txs = list_transactions(limit=8, sort_by="date", sort_order="desc")
if not recent_txs:
    st.info("No transactions recorded yet. Use the **Transactions** page to log your first income or expense!")
else:
    table_data = []
    for tx in recent_txs:
        icon = get_category_icon(tx.category)
        table_data.append({
            "Date": tx.transaction_date.strftime("%Y-%m-%d"),
            "Type": "🟢 Income" if tx.transaction_type == "Income" else "🔴 Expense",
            "Category": f"{icon} {tx.category}",
            "Description": tx.description or "-",
            "Amount": format_currency(tx.amount),
        })
    df_recent = pd.DataFrame(table_data)
    st.dataframe(df_recent, use_container_width=True, hide_index=True)
