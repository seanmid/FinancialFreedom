import streamlit as st
from database import init_db, get_db_connection
import pandas as pd
from datetime import datetime, date
from utils import calculate_monthly_savings, generate_spending_chart
from psycopg2.extras import RealDictCursor
from auth import init_auth, login_user, register_user, logout_user, require_auth

# Initialize the database
init_db()

# Page configuration
st.set_page_config(
    page_title="Budget Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize authentication
init_auth()

def show_login_page():
    st.title("Welcome to Budget Tracker")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                if login_user(username, password):
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register")

            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif register_user(new_username, new_password):
                    st.success("Registration successful! Please log in.")
                else:
                    st.error("Username already exists or registration failed")

def show_dashboard():
    user = require_auth()

    # Add navigation menu
    st.sidebar.title("Navigation")
    pages = {
        "Dashboard": "main",
        "Income & Expenses": "income_expenses",
        "Budget": "budget",
        "Analytics": "analytics",
        "Debt": "debt",
        "Payment Sources": "payment_sources"
    }

    if user.is_admin:
        pages["User Management"] = "user_management"

    # Add logout button
    if st.sidebar.button("Logout"):
        logout_user()
        st.rerun()

    st.title("💰 Financial Dashboard")
    st.write(f"Welcome back, {user.username}!")

    # Create columns for layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Quick Summary")

        # Get current month's data using direct PostgreSQL connection
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Calculate total income
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) as total_income 
            FROM income 
            WHERE DATE_TRUNC('month', date) = DATE_TRUNC('month', CURRENT_DATE)
            AND user_id = %s
        """, (user.id,))
        total_income = float(cur.fetchone()['total_income'])

        # Calculate total expenses
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) as total_expenses 
            FROM expenses 
            WHERE DATE_TRUNC('month', date) = DATE_TRUNC('month', CURRENT_DATE)
            AND user_id = %s
        """, (user.id,))
        total_expenses = float(cur.fetchone()['total_expenses'])

        # Display metrics
        st.metric("Monthly Income", f"${total_income:,.2f}")
        st.metric("Monthly Expenses", f"${total_expenses:,.2f}")
        st.metric("Monthly Savings", 
                 f"${calculate_monthly_savings(total_income, total_expenses):,.2f}",
                 delta=f"${total_income - total_expenses:,.2f}")

    with col2:
        st.subheader("Expense Breakdown")

        # Get expense categories
        cur.execute("""
            SELECT c.name as category, COALESCE(SUM(e.amount), 0) as amount
            FROM categories c
            LEFT JOIN expenses e ON c.id = e.category_id AND e.user_id = %s
            WHERE c.type = 'expense'
            AND (e.date IS NULL OR DATE_TRUNC('month', e.date) = DATE_TRUNC('month', CURRENT_DATE))
            GROUP BY c.name
            HAVING COALESCE(SUM(e.amount), 0) > 0
        """, (user.id,))
        category_expenses = pd.DataFrame(cur.fetchall())

        if not category_expenses.empty:
            fig = generate_spending_chart(category_expenses)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expenses recorded this month")

    # Recent Transactions
    st.subheader("Recent Transactions")

    cur.execute("""
        SELECT 'Expense' as type, e.description, e.amount, e.date, c.name as category
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s
        UNION ALL
        SELECT 'Income' as type, i.description, i.amount, i.date, c.name as category
        FROM income i
        JOIN categories c ON i.category_id = c.id
        WHERE i.user_id = %s
        ORDER BY date DESC
        LIMIT 5
    """, (user.id, user.id))

    recent_transactions = pd.DataFrame(cur.fetchall())

    if not recent_transactions.empty:
        st.dataframe(
            recent_transactions,
            column_config={
                "type": "Transaction Type",
                "description": "Description",
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    format="$%.2f"
                ),
                "date": "Date",
                "category": "Category"
            },
            hide_index=True
        )
    else:
        st.info("No recent transactions")

    cur.close()
    conn.close()

def main():
    if not st.session_state.user:
        show_login_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()