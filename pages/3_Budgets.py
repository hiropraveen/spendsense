"""
SpendSense — Budgets Management Page
Create, track, edit, and evaluate monthly category budgets against actual student expenses.
"""

from datetime import datetime
from decimal import Decimal
import streamlit as st
import pandas as pd
from config import (
    APP_TITLE,
    EXPENSE_CATEGORIES,
    CURRENCY_SYMBOL,
    format_currency,
    get_category_icon,
)
from ui_utils import (
    apply_custom_css,
    render_sidebar,
    render_page_header,
    render_metric_card,
    check_database_status,
)
from schemas import BudgetCreate, BudgetUpdate
from services.budget_service import (
    create_budget,
    update_budget,
    delete_budget,
    get_budget_status_for_month,
    get_monthly_budget_summary,
)

st.set_page_config(
    page_title=f"Budgets — {APP_TITLE}",
    page_icon="🎯",
    layout="wide",
)

apply_custom_css()
render_sidebar()

render_page_header("🎯 Monthly Budget Tracking", "Set category spending limits, track burn rate, and get real-time overspending alerts.")

is_connected, db_msg = check_database_status()
if not is_connected:
    st.warning(f"⚠️ **Database Connection Required**\n\n{db_msg}")
    st.info("Configure your Neon database in the **⚙️ Settings** page to set and monitor budgets.")
    st.stop()

# Month and Year selection
now = datetime.now()
b_col1, b_col2, b_col3 = st.columns([2, 2, 2])

with b_col1:
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    sel_month_name = st.selectbox(
        "Select Month",
        options=month_names,
        index=now.month - 1,
        key="budget_month_select",
    )
    sel_month = month_names.index(sel_month_name) + 1

with b_col2:
    years = list(range(now.year - 3, now.year + 2))
    sel_year = st.selectbox(
        "Select Year",
        options=years,
        index=years.index(now.year) if now.year in years else 0,
        key="budget_year_select",
    )

with b_col3:
    st.write("")
    st.write("")
    if st.button("🔄 Refresh Budgets", use_container_width=True):
        st.rerun()

st.write("")

# Budget summary cards
summary = get_monthly_budget_summary(sel_year, sel_month)
m1, m2, m3, m4 = st.columns(4)

render_metric_card(
    m1,
    "Allocated Budget",
    format_currency(summary["total_allocated_budget"]),
    f"Target for {sel_month_name} {sel_year}",
    "budget",
)
render_metric_card(
    m2,
    "Total Expenses",
    format_currency(summary["total_expenses"]),
    "All expense records",
    "expense",
)
rem_budget = summary["total_allocated_budget"] - summary["total_spent_budgeted"]
render_metric_card(
    m3,
    "Remaining Budget",
    format_currency(rem_budget),
    "For budgeted categories",
    "balance" if rem_budget >= 0 else "expense",
)
render_metric_card(
    m4,
    "Alerts",
    f"{summary['exceeded_count']} Exceeded",
    f"{summary['warning_count']} approaching limit",
    "expense" if summary["exceeded_count"] > 0 else ("warning" if summary["warning_count"] > 0 else "income"),
)

st.write("")

# Tabs: "📊 Active Budgets", "➕ Create Category Budget"
tab_active, tab_create = st.tabs(["📊 Active Category Budgets", "➕ Set New Budget"])

with tab_create:
    st.subheader(f"Set Budget for {sel_month_name} {sel_year}")
    
    with st.form("create_budget_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            cat_choice = st.selectbox(
                "Expense Category",
                options=EXPENSE_CATEGORIES,
                format_func=lambda c: f"{get_category_icon(c)} {c}",
            )
        with f_col2:
            budget_amount = st.number_input(
                f"Monthly Budget Limit ({CURRENCY_SYMBOL})",
                min_value=50.0,
                max_value=1000000.0,
                step=100.0,
                value=2000.0,
            )

        submit_budget = st.form_submit_button("💾 Save Budget", use_container_width=True)
        if submit_budget:
            try:
                dec_amt = Decimal(str(budget_amount))
                payload = BudgetCreate(
                    category=cat_choice,
                    amount=dec_amt,
                    budget_month=sel_month,
                    budget_year=sel_year,
                )
                create_budget(payload)
                st.success(f"✅ Budget of {format_currency(dec_amt)} set for '{cat_choice}' in {sel_month_name} {sel_year}.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to set budget: {str(e)}")

with tab_active:
    statuses = summary["statuses"]
    if not statuses:
        st.info(f"No budgets configured yet for {sel_month_name} {sel_year}. Use the 'Set New Budget' tab to set category spending limits.")
    else:
        st.subheader("Category Budget Breakdown")
        
        for item in statuses:
            cat = item["category"]
            icon = get_category_icon(cat)
            b_amt = item["budget_amount"]
            spent = item["actual_spent"]
            rem = item["remaining"]
            pct = item["utilization_pct"]
            status = item["status"]

            # Visual status indicator
            if status == "EXCEEDED":
                badge = f'<span class="badge badge-exceeded">🚨 Exceeded ({pct:.1f}%)</span>'
                bar_val = 1.0
            elif status == "WARNING":
                badge = f'<span class="badge badge-warning">⚠️ Near Limit ({pct:.1f}%)</span>'
                bar_val = min(pct / 100.0, 1.0)
            else:
                badge = f'<span class="badge badge-income">✅ On Track ({pct:.1f}%)</span>'
                bar_val = min(pct / 100.0, 1.0)

            with st.container():
                st.markdown(
                    f"""
                    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px 20px; margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span style="font-size: 1.15rem; font-weight: 700; color: #1e293b;">{icon} {cat}</span>
                            {badge}
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.9rem; color: #64748b; margin-bottom: 6px;">
                            <span>Spent: <b>{format_currency(spent)}</b></span>
                            <span>Budget: <b>{format_currency(b_amt)}</b></span>
                            <span>Remaining: <b style="color: {'#ef4444' if rem < 0 else '#10b981'};">{format_currency(rem)}</b></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.progress(bar_val)

                # Edit / Delete controls in an expander
                with st.expander(f"⚙️ Manage {cat} Budget (ID #{item['id']})"):
                    col_u1, col_u2 = st.columns([2, 1])
                    with col_u1:
                        new_amt_val = st.number_input(
                            f"Update Limit ({CURRENCY_SYMBOL})",
                            min_value=1.0,
                            value=float(b_amt),
                            step=100.0,
                            key=f"edit_amt_{item['id']}",
                        )
                        if st.button("💾 Update Limit", key=f"btn_upd_{item['id']}"):
                            try:
                                update_budget(item["id"], BudgetUpdate(amount=Decimal(str(new_amt_val))))
                                st.success(f"Budget for {cat} updated to {format_currency(Decimal(str(new_amt_val)))}.")
                                st.rerun()
                            except Exception as ex:
                                st.error(str(ex))

                    with col_u2:
                        st.write("Danger Zone")
                        if st.button("🗑️ Delete Budget", key=f"btn_bdel_{item['id']}", type="secondary"):
                            delete_budget(item["id"])
                            st.success(f"Budget for {cat} deleted.")
                            st.rerun()

                st.write("")
