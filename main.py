import streamlit as st
from database import init_db, get_db_connection
import pandas as pd
from datetime import datetime, date
from utils import calculate_monthly_savings, generate_spending_chart
from psycopg2.extras import RealDictCursor

# Initialize the database
init_db()

# Page configuration
st.set_page_config(
    page_title="Budget Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Main dashboard
def main():
    st.title("💰 Financial Dashboard")

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
        """)
        total_income = float(cur.fetchone()['total_income'])

        # Calculate total expenses
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) as total_expenses 
            FROM expenses 
            WHERE DATE_TRUNC('month', date) = DATE_TRUNC('month', CURRENT_DATE)
        """)
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
            LEFT JOIN expenses e ON c.id = e.category_id
            WHERE c.type = 'expense'
            AND (e.date IS NULL OR DATE_TRUNC('month', e.date) = DATE_TRUNC('month', CURRENT_DATE))
            GROUP BY c.name
            HAVING COALESCE(SUM(e.amount), 0) > 0
        """)
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
        UNION ALL
        SELECT 'Income' as type, i.description, i.amount, i.date, c.name as category
        FROM income i
        JOIN categories c ON i.category_id = c.id
        ORDER BY date DESC
        LIMIT 5
    """)

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

if __name__ == "__main__":
    main()