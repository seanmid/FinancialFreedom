import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from database import get_db_connection
from utils import export_to_csv
from datetime import datetime, timedelta
from auth import require_auth, logout_user
from components import add_auth_controls

def analytics_page():
    # Ensure user is logged in
    user = require_auth()
    if not user:
        st.stop()  # Stop execution if user is not logged in

    st.title("Financial Analytics")

    # Add authentication controls
    add_auth_controls()

    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())

    # Remove duplicate logout button
    # Get data from database
    conn = get_db_connection()
    cur = conn.cursor()

    # Income data
    cur.execute(
        """
        SELECT i.date, i.amount, c.name as category
        FROM income i
        JOIN categories c ON i.category_id = c.id
        WHERE i.date BETWEEN %s AND %s
        AND i.user_id = %s
        """,
        (start_date, end_date, user.id)
    )
    income_data = cur.fetchall()

    # Expense data with payment sources
    cur.execute(
        """
        SELECT e.date, e.amount, c.name as category, 
               e.necessity_level, ps.name as payment_source,
               ps.type as source_type, ps.bank_name
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        LEFT JOIN payment_sources ps ON e.payment_source_id = ps.id
        WHERE e.date BETWEEN %s AND %s
        AND e.user_id = %s
        """,
        (start_date, end_date, user.id)
    )
    expense_data = cur.fetchall()

    # Convert to DataFrames
    income_df = pd.DataFrame(income_data, columns=['date', 'amount', 'category'])
    expense_df = pd.DataFrame(expense_data, columns=['date', 'amount', 'category', 
                                                   'necessity_level', 'payment_source',
                                                   'source_type', 'bank_name'])

    # Summary metrics
    total_income = income_df['amount'].sum() if not income_df.empty else 0
    total_expenses = expense_df['amount'].sum() if not expense_df.empty else 0
    savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0

    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Income", f"${total_income:,.2f}")
    with col2:
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
    with col3:
        st.metric("Savings Rate", f"{savings_rate:.1f}%")

    # Visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Income Analysis", "Expense Analysis", "Payment Sources", "Trends"])

    with tab1:
        if not income_df.empty:
            # Income by category
            income_by_category = income_df.groupby('category')['amount'].sum().reset_index()
            fig = px.pie(
                income_by_category,
                values='amount',
                names='category',
                title="Income Distribution by Category"
            )
            st.plotly_chart(fig)

            # Income over time
            income_by_date = income_df.groupby('date')['amount'].sum().reset_index()
            fig = px.line(
                income_by_date,
                x='date',
                y='amount',
                title="Income Trend"
            )
            st.plotly_chart(fig)
        else:
            st.info("No income data available for the selected period")

    with tab2:
        if not expense_df.empty:
            # Expenses by category
            expense_by_category = expense_df.groupby('category')['amount'].sum().reset_index()
            fig = px.pie(
                expense_by_category,
                values='amount',
                names='category',
                title="Expense Distribution by Category"
            )
            st.plotly_chart(fig)

            # Expenses by necessity level
            expense_by_necessity = expense_df.groupby('necessity_level')['amount'].sum().reset_index()
            fig = px.bar(
                expense_by_necessity,
                x='necessity_level',
                y='amount',
                title="Expenses by Necessity Level"
            )
            st.plotly_chart(fig)
        else:
            st.info("No expense data available for the selected period")

    with tab3:
        if not expense_df.empty:
            # Expenses by payment source
            st.subheader("Payment Source Analysis")

            # By payment source
            expense_by_source = expense_df.groupby(['payment_source', 'bank_name'])['amount'].sum().reset_index()
            fig = px.bar(
                expense_by_source,
                x='payment_source',
                y='amount',
                color='bank_name',
                title="Expenses by Payment Source"
            )
            st.plotly_chart(fig)

            # By source type
            expense_by_source_type = expense_df.groupby('source_type')['amount'].sum().reset_index()
            fig = px.pie(
                expense_by_source_type,
                values='amount',
                names='source_type',
                title="Payment Method Distribution"
            )
            st.plotly_chart(fig)
        else:
            st.info("No expense data available for the selected period")

    with tab4:
        if not income_df.empty or not expense_df.empty:
            # Combined income vs expenses trend
            income_trend = income_df.groupby('date')['amount'].sum().reset_index() if not income_df.empty else pd.DataFrame({'date': [], 'amount': []})
            income_trend['type'] = 'Income'
            expense_trend = expense_df.groupby('date')['amount'].sum().reset_index() if not expense_df.empty else pd.DataFrame({'date': [], 'amount': []})
            expense_trend['type'] = 'Expense'

            combined_trend = pd.concat([income_trend, expense_trend])

            if not combined_trend.empty:
                fig = px.line(
                    combined_trend,
                    x='date',
                    y='amount',
                    color='type',
                    title="Income vs Expenses Over Time"
                )
                st.plotly_chart(fig)
        else:
            st.info("No data available for the selected period")

    # Export options
    st.subheader("Export Data")

    col1, col2 = st.columns(2)

    with col1:
        if not income_df.empty and st.button("Export Income Data"):
            csv = export_to_csv(income_df, "income_data.csv")
            st.download_button(
                label="Download Income CSV",
                data=csv,
                file_name="income_data.csv",
                mime="text/csv"
            )

    with col2:
        if not expense_df.empty and st.button("Export Expense Data"):
            csv = export_to_csv(expense_df, "expense_data.csv")
            st.download_button(
                label="Download Expense CSV",
                data=csv,
                file_name="expense_data.csv",
                mime="text/csv"
            )

    cur.close()
    conn.close()

if __name__ == "__main__":
    analytics_page()