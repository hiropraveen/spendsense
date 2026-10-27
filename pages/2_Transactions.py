"""
SpendSense — Transactions Page
Complete CRUD: Log new income or expenses, filter, search, edit, and delete transactions.
"""

from datetime import date, datetime
from decimal import Decimal
import streamlit as st
import pandas as pd
from config import (
    APP_TITLE,
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    CURRENCY_SYMBOL,
    format_currency,
    get_category_icon,
)
from ui_utils import (
    apply_custom_css,
    render_sidebar,
    render_page_header,
    check_database_status,
)
from schemas import TransactionCreate, TransactionUpdate
from services.transaction_service import (
    create_transaction,
    list_transactions,
    get_transaction_by_id,
    update_transaction,
    delete_transaction,
)

st.set_page_config(
    page_title=f"Transactions — {APP_TITLE}",
    page_icon="💸",
    layout="wide",
)

apply_custom_css()
render_sidebar()

render_page_header("💸 Transactions Management", "Record, inspect, edit, and manage all your student cash flows.")

is_connected, db_msg = check_database_status()
if not is_connected:
    st.warning(f"⚠️ **Database Connection Required**\n\n{db_msg}")
    st.info("Configure your Neon database in the **⚙️ Settings** page to start tracking transactions.")
    st.stop()

# Action Tabs: "📜 All Transactions", "➕ Add Transaction", "✏️ Edit / Delete"
tab_list, tab_add = st.tabs(["📜 Transaction History", "➕ Add New Transaction"])

with tab_add:
    st.subheader("Record a Transaction")
    
    with st.form("add_transaction_form", clear_on_submit=True):
        col_type, col_amt, col_date = st.columns(3)

        with col_type:
            tx_type = st.radio(
                "Transaction Type",
                options=["Expense", "Income"],
                horizontal=True,
                index=0,
            )

        with col_amt:
            amt_input = st.number_input(
                f"Amount ({CURRENCY_SYMBOL})",
                min_value=0.01,
                max_value=1000000.00,
                step=10.0,
                format="%.2f",
                value=100.0,
            )

        with col_date:
            tx_date = st.date_input("Transaction Date", value=date.today())

        # Category options based on transaction type
        categories = EXPENSE_CATEGORIES if tx_type == "Expense" else INCOME_CATEGORIES
        col_cat, col_desc = st.columns([1, 2])

        with col_cat:
            cat_selected = st.selectbox(
                "Category",
                options=categories,
                format_func=lambda c: f"{get_category_icon(c)} {c}",
            )

        with col_desc:
            desc_input = st.text_input("Description / Notes (Optional)", placeholder="e.g. Lunch at cafeteria or tuition stipend")

        submitted = st.form_submit_button("💾 Save Transaction", use_container_width=True)

        if submitted:
            try:
                dec_amt = Decimal(str(amt_input))
                payload = TransactionCreate(
                    transaction_type=tx_type,
                    amount=dec_amt,
                    category=cat_selected,
                    transaction_date=tx_date,
                    description=desc_input.strip() if desc_input else None,
                )
                created = create_transaction(payload)
                st.success(f"✅ Successfully recorded {tx_type} of {format_currency(created.amount)} under '{created.category}'.")
            except Exception as e:
                st.error(f"❌ Failed to record transaction: {str(e)}")

with tab_list:
    st.subheader("Filter and Search")
    
    # Filter controls
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)

    with f_col1:
        type_filter = st.selectbox("Type", options=["All", "Income", "Expense"], index=0)

    with f_col2:
        all_unique_cats = ["All"] + sorted(list(set(EXPENSE_CATEGORIES + INCOME_CATEGORIES)))
        cat_filter = st.selectbox("Category", options=all_unique_cats, index=0)

    with f_col3:
        d_start = st.date_input("Start Date", value=None)

    with f_col4:
        d_end = st.date_input("End Date", value=None)

    s_col1, s_col2, s_col3 = st.columns([3, 1.5, 1])
    with s_col1:
        search_kw = st.text_input("🔍 Search Description or Category", placeholder="Type keywords...")

    with s_col2:
        sort_choice = st.selectbox("Sort By", options=["Date (Newest first)", "Date (Oldest first)", "Amount (Highest first)", "Amount (Lowest first)"])

    with s_col3:
        st.write("")
        st.write("")
        clear_btn = st.button("Reset Filters", use_container_width=True)
        if clear_btn:
            st.rerun()

    # Determine sorting parameters
    if sort_choice == "Date (Newest first)":
        sort_by, sort_order = "date", "desc"
    elif sort_choice == "Date (Oldest first)":
        sort_by, sort_order = "date", "asc"
    elif sort_choice == "Amount (Highest first)":
        sort_by, sort_order = "amount", "desc"
    else:
        sort_by, sort_order = "amount", "asc"

    transactions = list_transactions(
        start_date=d_start,
        end_date=d_end,
        category=cat_filter,
        transaction_type=type_filter,
        search=search_kw,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    st.write("")
    st.write(f"Showing **{len(transactions)}** transaction(s)")

    if not transactions:
        st.info("No transactions match the selected filters.")
    else:
        # Display transaction list with Edit / Delete actions
        for tx in transactions:
            icon = get_category_icon(tx.category)
            type_badge = "🟢 Income" if tx.transaction_type == "Income" else "🔴 Expense"
            amt_display = format_currency(tx.amount)

            with st.expander(f"{icon} {tx.transaction_date.strftime('%d %b %Y')} — {tx.category}: {amt_display} ({tx.transaction_type})"):
                c_details, c_actions = st.columns([3, 1])

                with c_details:
                    st.write(f"**Type:** {type_badge}")
                    st.write(f"**Amount:** {amt_display}")
                    st.write(f"**Category:** {icon} {tx.category}")
                    st.write(f"**Date:** {tx.transaction_date.strftime('%A, %d %B %Y')}")
                    st.write(f"**Notes:** {tx.description or 'None'}")
                    st.caption(f"ID: #{tx.id} | Recorded: {tx.created_at.strftime('%Y-%m-%d %H:%M:%S') if tx.created_at else '-'}")

                with c_actions:
                    st.write("**Manage Record**")
                    
                    # Edit trigger
                    edit_key = f"edit_toggle_{tx.id}"
                    if st.button("✏️ Edit", key=f"btn_edit_{tx.id}", use_container_width=True):
                        st.session_state[edit_key] = not st.session_state.get(edit_key, False)

                    # Delete trigger
                    delete_key = f"delete_confirm_{tx.id}"
                    if st.button("🗑️ Delete", key=f"btn_del_{tx.id}", use_container_width=True):
                        st.session_state[delete_key] = True

                # If delete requested, show confirmation
                if st.session_state.get(f"delete_confirm_{tx.id}", False):
                    st.warning(f"Are you sure you want to delete transaction #{tx.id} ({format_currency(tx.amount)})?")
                    c_yes, c_no = st.columns(2)
                    with c_yes:
                        if st.button("Yes, Delete", key=f"confirm_yes_{tx.id}", type="primary", use_container_width=True):
                            delete_transaction(tx.id)
                            st.session_state[f"delete_confirm_{tx.id}"] = False
                            st.success(f"Transaction #{tx.id} deleted.")
                            st.rerun()
                    with c_no:
                        if st.button("Cancel", key=f"confirm_no_{tx.id}", use_container_width=True):
                            st.session_state[f"delete_confirm_{tx.id}"] = False
                            st.rerun()

                # If edit requested, show prefilled form
                if st.session_state.get(f"edit_toggle_{tx.id}", False):
                    st.markdown("---")
                    st.markdown("##### ✏️ Edit Transaction")
                    with st.form(f"form_edit_{tx.id}"):
                        e_c1, e_c2, e_c3 = st.columns(3)
                        with e_c1:
                            new_type = st.radio("Type", ["Expense", "Income"], index=0 if tx.transaction_type == "Expense" else 1, key=f"e_type_{tx.id}")
                        with e_c2:
                            new_amt = st.number_input(f"Amount ({CURRENCY_SYMBOL})", min_value=0.01, value=float(tx.amount), format="%.2f", key=f"e_amt_{tx.id}")
                        with e_c3:
                            new_date = st.date_input("Date", value=tx.transaction_date, key=f"e_date_{tx.id}")

                        avail_cats = EXPENSE_CATEGORIES if new_type == "Expense" else INCOME_CATEGORIES
                        curr_cat_idx = avail_cats.index(tx.category) if tx.category in avail_cats else 0
                        new_cat = st.selectbox("Category", options=avail_cats, index=curr_cat_idx, key=f"e_cat_{tx.id}")
                        new_desc = st.text_input("Description", value=tx.description or "", key=f"e_desc_{tx.id}")

                        if st.form_submit_button("Update Transaction"):
                            try:
                                update_transaction(
                                    tx.id,
                                    TransactionUpdate(
                                        transaction_type=new_type,
                                        amount=Decimal(str(new_amt)),
                                        category=new_cat,
                                        transaction_date=new_date,
                                        description=new_desc,
                                    ),
                                )
                                st.session_state[f"edit_toggle_{tx.id}"] = False
                                st.success("Transaction updated successfully!")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Failed to update: {str(ex)}")
