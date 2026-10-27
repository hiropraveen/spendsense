"""
SpendSense — Settings & About Page
Inspect Neon database status, configure connection, and view project documentation.
"""

import os
from pathlib import Path
import streamlit as st
from config import APP_TITLE, APP_SUBTITLE, mask_database_url
from ui_utils import (
    apply_custom_css,
    render_sidebar,
    render_page_header,
    check_database_status,
)
from database import test_connection, init_db, reset_engine

st.set_page_config(
    page_title=f"Settings & About — {APP_TITLE}",
    page_icon="⚙️",
    layout="wide",
)

apply_custom_css()
render_sidebar()

render_page_header("⚙️ Settings & Database Management", "Monitor connection health, update database credentials, and learn about SpendSense.")

tab_db, tab_about = st.tabs(["🔌 Database Configuration", "ℹ️ About SpendSense"])

with tab_db:
    st.subheader("Neon PostgreSQL Database Connection")

    # Current status
    current_url = os.getenv("DATABASE_URL", "").strip()
    is_connected, db_msg = test_connection()

    if is_connected:
        st.success(f"🟢 **Status: Online** — {db_msg}")
    else:
        st.warning(f"🟡 **Status: Action Required** — {db_msg}")

    st.write(f"**Configured Connection URL:** `{mask_database_url(current_url)}`")

    st.write("")
    if st.button("🧪 Test Connection (SELECT 1)", use_container_width=False):
        with st.spinner("Testing connection to Neon PostgreSQL..."):
            reset_engine()
            success, msg = test_connection()
            if success:
                st.session_state["db_connected"] = True
                st.session_state["db_msg"] = msg
                init_db()
                st.success(f"✅ Success: {msg}")
            else:
                st.session_state["db_connected"] = False
                st.session_state["db_msg"] = msg
                st.error(f"❌ Connection failed: {msg}")

    st.markdown("---")
    st.subheader("Update Database Password / URL")
    st.caption("You can update your connection string or database password here. It will update the local `.env` securely.")

    with st.form("update_env_form"):
        new_password = st.text_input(
            "Neon Database Password",
            type="password",
            placeholder="Enter your Neon PostgreSQL password",
            help="Your password will be securely inserted into the Neon connection URL in your local .env file.",
        )
        submit_pw = st.form_submit_button("💾 Save Password to .env")

        if submit_pw:
            if not new_password.strip():
                st.error("Please enter a valid password.")
            else:
                env_path = Path(".env")
                env_content = f'DATABASE_URL="postgresql://neondb_owner:{new_password.strip()}@ep-super-field-b5m0wd70-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"\n'
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(env_content)

                os.environ["DATABASE_URL"] = env_content.split("=", 1)[1].strip().strip('"')
                reset_engine()
                st.session_state.pop("db_connected", None)
                st.session_state.pop("db_msg", None)
                st.success("✅ Password saved to .env! Testing new connection...")
                st.rerun()

with tab_about:
    st.subheader("About SpendSense")
    st.markdown(
        f"""
        **{APP_TITLE}** is a full-stack, database-connected student financial management web application.
        
        Designed to empower college students to manage pocket money, stipends, and day-to-day expenditures with clarity and discipline.
        
        ### 🛠️ Architecture & Tech Stack
        - **Frontend UI:** Streamlit with custom CSS design tokens & Plotly interactive visualizers
        - **Database:** PostgreSQL on Neon Serverless Cloud
        - **ORM & Sessions:** SQLAlchemy 2.0 with connection pooling and SSL encryption
        - **Driver:** psycopg 3 (binary)
        - **Data Validation:** Pydantic models for strict boundary enforcement
        - **Math & Money:** PostgreSQL `NUMERIC` and Python `Decimal` (zero floating-point rounding errors)
        - **Testing:** Pytest with isolated in-memory test database fixtures

        ### 🛡️ Privacy & Safety Guarantees
        - **No credential leakage:** Connection strings are automatically masked in all UI views and system logs.
        - **Safe initialization:** Schema checks never drop, wipe, or overwrite existing tables.
        - **Isolated testing:** Automated test runs execute against in-memory fixtures without touching live Neon data.
        """
    )
