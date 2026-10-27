# SpendSense — Smart Student Expense Tracker

A full-stack, database-connected personal finance web application built specifically for college students to track income, daily expenses, monthly category budgets, account balances, and spending patterns.

SpendSense connects directly to **Neon Serverless PostgreSQL** and features an interactive financial intelligence dashboard built with **Streamlit** and **Plotly**.

---

## 🚀 Key Features

- **📊 Comprehensive Monthly Dashboard**
  - Instant KPI cards for Total Income, Total Expenses, Remaining Balance, and Allocated Budgets.
  - Overall budget utilization percentage and real-time limit alerts.
  - Recent transaction feed and interactive Plotly visualization charts.
  - Formatted in Indian Rupees (`₹`).

- **💸 Full Transaction Management (CRUD)**
  - Record Income (Salary, Allowance, Scholarship, Freelancing, Other).
  - Record Expenses (Food, Transportation, Education, Shopping, Rent, Bills, Healthcare, Entertainment, Other).
  - Filter transactions by type, category, date range, or keyword search.
  - Edit existing transactions or delete records with confirmation safeguards.
  - Precise calculations using PostgreSQL `NUMERIC` and Python `Decimal` (zero floating-point errors).

- **🎯 Monthly Category Budgets & Overspending Alerts**
  - Set category spending limits per month and year.
  - Automatic burn-rate calculation against live PostgreSQL expense transactions.
  - Visual status badges and progress bars:
    - 🟢 **On Track** (< 80% used)
    - 🟡 **Near Limit / Warning** (80% - 100% used)
    - 🔴 **Exceeded** (> 100% used)
  - Edit or delete category budgets with database unique constraints preventing accidental duplicates.

- **📈 Advanced Financial Analytics (Plotly)**
  - **Expense Distribution**: Donut chart with category percentages and hover details.
  - **Monthly Income vs Expense**: Grouped bar chart tracking monthly cash flow over 3, 6, or 12 months.
  - **Spending Trend**: Cumulative and daily spending line chart showing burn rate over time.
  - **Budget vs Actual**: Visual comparison highlighting categories exceeding limits.

- **⚙️ Settings & Connection Health**
  - Built-in `SELECT 1` database health check.
  - Secure credential management with automatic masking (`postgresql://user:*****@host...`).
  - Update `.env` connection directly from the UI without manual file edits.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11+ / 3.13 |
| **Frontend UI** | Streamlit |
| **Data Visualizations** | Plotly Express & Plotly Graph Objects |
| **Database** | PostgreSQL hosted on Neon Serverless Cloud |
| **ORM & Pooling** | SQLAlchemy 2.0 |
| **Database Driver** | psycopg 3 (binary) |
| **Validation** | Pydantic v2 |
| **Data Processing** | Pandas |
| **Testing** | Pytest (Isolated in-memory SQLite fixtures) |

---

## 💻 Windows Setup & Execution Instructions

### 1. Clone or Open the Project
Open Windows PowerShell in the project directory:
```powershell
cd c:\Users\LENOVO\Downloads\spendsense
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once).*

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Neon PostgreSQL Database Connection
Copy the example environment file:
```powershell
cp .env.example .env
```

Edit `.env` and set your Neon PostgreSQL connection string:
```dotenv
DATABASE_URL="postgresql://neondb_owner:<YOUR_NEON_PASSWORD>@ep-super-field-b5m0wd70-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
```
> **Security Note:** Replace `<YOUR_NEON_PASSWORD>` with your database password. `.env` is listed in `.gitignore` and credentials will never be committed to GitHub or displayed in UI logs.

### 5. Launch SpendSense
```powershell
streamlit run app.py
```
SpendSense will open in your browser at `http://localhost:8501`.

---

## 🧪 Running Automated Tests

Run the test suite using pytest:
```powershell
.\venv\Scripts\pytest -v
```

All 15 verification areas are thoroughly tested:
1. Income transaction creation
2. Expense transaction creation
3. Rejection of zero and negative amounts
4. Transaction editing
5. Transaction deletion
6. Handling nonexistent records
7. Monthly income calculation
8. Monthly expense calculation
9. Balance calculation
10. Category-wise expense grouping
11. Budget utilization calculation
12. Budget warning threshold behavior (Normal, Warning, Exceeded)
13. Transaction filtering and sorting
14. Empty database handling (safe return of zero balances)
15. Connection error and credential masking safeguards

> **Database Safety Guarantee:** Automated tests run against isolated in-memory SQLite test fixtures. They will **never** modify or delete financial records in your production Neon database.

---

## 📁 Project Structure

```text
spendsense/
├── app.py                      # Application entrypoint & multi-page router
├── database.py                 # Neon PostgreSQL connection, pooling, health check
├── models.py                   # SQLAlchemy models (Transaction, Budget)
├── schemas.py                  # Pydantic validation schemas
├── config.py                   # Constants, categories, icons, currency formatter
├── ui_utils.py                 # CSS styling, metric cards, sidebar monitor
├── requirements.txt            # Python dependencies
├── .env                        # Local database credentials (ignored by git)
├── .env.example                # Template for environment variables
├── .gitignore                  # Git ignore rules
├── README.md                   # Setup and usage documentation
├── services/
│   ├── __init__.py
│   ├── transaction_service.py  # Transaction CRUD & monthly sums
│   ├── budget_service.py       # Budget CRUD & burn-rate alerts
│   └── analytics_service.py    # Plotly visualization builders
├── pages/
│   ├── 1_Dashboard.py          # Monthly overview & recent activity
│   ├── 2_Transactions.py       # Full CRUD transactions & filters
│   ├── 3_Budgets.py            # Category budgets & utilization
│   ├── 4_Analytics.py          # Plotly charts & spending trends
│   └── 5_Settings.py           # DB health check (SELECT 1) & config
└── tests/
    ├── conftest.py             # Isolated in-memory DB fixture
    ├── test_transactions.py    # Transaction tests
    ├── test_budgets.py         # Budget tests
    └── test_calculations.py    # Calculation & security tests
```

---

## 🛡️ Database Safety & Integrity

- **Non-destructive Initialization:** Tables are verified and created using `checkfirst=True`. SpendSense **never** drops tables or clears existing rows during startup.
- **Fail-safe Feedback:** If Neon is temporarily unreachable or the password needs updating, SpendSense displays a clear status banner without crashing or exposing database credentials.
