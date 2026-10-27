"""
SpendSense — Smart Student Expense Tracker
Main application entry point.
"""

import streamlit as st

st.set_page_config(
    page_title="SpendSense — Smart Student Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Redirect to the main Dashboard page
try:
    st.switch_page("pages/1_Dashboard.py")
except Exception:
    st.write("Welcome to SpendSense! Please navigate to **Dashboard** using the sidebar.")
