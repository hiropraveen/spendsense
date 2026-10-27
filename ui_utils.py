"""
Reusable UI utilities, styling, and database connection checks for SpendSense.
"""

from datetime import datetime
import streamlit as st
from config import APP_TITLE, APP_SUBTITLE, CURRENCY_SYMBOL
from database import test_connection, init_db


def apply_custom_css():
    """Apply professional, modern styling across the application."""
    st.markdown(
        """
        <style>
        /* Modern font imports */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Metric cards */
        .metric-card {
            background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 20px 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            transition: all 0.25s ease-in-out;
            margin-bottom: 12px;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
            border-color: #cbd5e1;
        }
        .metric-label {
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 1.85rem;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.02em;
        }
        .metric-value.income { color: #10b981; }
        .metric-value.expense { color: #ef4444; }
        .metric-value.balance { color: #3b82f6; }
        .metric-value.budget { color: #8b5cf6; }
        .metric-sub {
            font-size: 0.8rem;
            color: #94a3b8;
            margin-top: 6px;
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .badge-income { background-color: #d1fae5; color: #065f46; }
        .badge-expense { background-color: #fee2e2; color: #991b1b; }
        .badge-normal { background-color: #dbeafe; color: #1e40af; }
        .badge-warning { background-color: #fef3c7; color: #92400e; }
        .badge-exceeded { background-color: #fee2e2; color: #991b1b; }

        /* Sidebar brand */
        .sidebar-brand {
            padding: 12px 0 20px 0;
            border-bottom: 1px solid #e2e8f0;
            margin-bottom: 20px;
        }
        .sidebar-title {
            font-size: 1.45rem;
            font-weight: 800;
            color: #1e293b;
            margin: 0;
        }
        .sidebar-subtitle {
            font-size: 0.8rem;
            color: #64748b;
            margin-top: 2px;
        }

        /* Status pill */
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.82rem;
            font-weight: 600;
            margin-top: 10px;
        }
        .status-pill.online {
            background-color: #ecfdf5;
            color: #047857;
            border: 1px solid #a7f3d0;
        }
        .status-pill.offline {
            background-color: #fffbeb;
            color: #b45309;
            border: 1px solid #fde68a;
        }

        /* Tables */
        .dataframe {
            border-radius: 8px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def check_database_status():
    """
    Check database connectivity and initialize tables if needed.
    Returns (is_connected, message).
    """
    if "db_connected" not in st.session_state:
        connected, msg = test_connection()
        st.session_state["db_connected"] = connected
        st.session_state["db_msg"] = msg
        if connected:
            try:
                init_db()
            except Exception as e:
                st.session_state["db_connected"] = False
                st.session_state["db_msg"] = f"Table initialization error: {str(e)}"

    return st.session_state.get("db_connected", False), st.session_state.get("db_msg", "")


def render_sidebar():
    """Render the sidebar branding and database health monitor."""
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                <div class="sidebar-title">💰 {APP_TITLE}</div>
                <div class="sidebar-subtitle">{APP_SUBTITLE}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        is_connected, msg = check_database_status()
        if is_connected:
            st.markdown(
                """
                <div class="status-pill online">
                    <span>🟢</span> <b>Neon PostgreSQL: Connected</b>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="status-pill offline">
                    <span>🟡</span> <b>Neon PostgreSQL: Setup Required</b>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("Go to **5_Settings** or update `.env` with your Neon password.")

        st.markdown("---")


def render_page_header(title: str, subtitle: str = ""):
    """Render a clean standard page header."""
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.write("")


def render_metric_card(col, label: str, value_str: str, sub_str: str = "", card_type: str = ""):
    """Render a high-end financial metric card."""
    col.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value {card_type}">{value_str}</div>
            <div class="metric-sub">{sub_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
