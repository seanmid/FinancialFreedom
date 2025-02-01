import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from database import get_db_connection
from utils import export_to_csv
from datetime import datetime, timedelta

def analytics_page():
    st.title("Financial Analytics")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
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
        """,
        (start_date, end_date)
    )
    income_data = cur.fetchall()
    
    # Expense data
    cur.execute(
        """
        SELECT e.date, e.amount, c.name as category, e.necessity_level
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.date BETWEEN %s AND %s
        """,
        (start_date, end_date)
    )
    expense_data = cur.fetchall()
    
    # Convert to DataFrames
    income_df = pd.DataFrame(income_data, columns=['date', 'amount', 'category'])
    expense_df = pd.DataFrame(expense_data, columns=['date', 'amount', 'category', 'necessity_level'])
    
    # Summary metrics
    total_income = income_df['amount'].sum()
    total_expenses = expense_df['amount'].sum()
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
    tab1, tab2, tab3 = st.tabs(["Income Analysis", "Expense Analysis", "Trends"])
    
    with tab1:
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
    
    with tab2:
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
    
    with tab3:
        # Combined income vs expenses trend
        income_trend = income_df.groupby('date')['amount'].sum().reset_index()
        income_trend['type'] = 'Income'
        expense_trend = expense_df.groupby('date')['amount'].sum().reset_index()
        expense_trend['type'] = 'Expense'
        
        combined_trend = pd.concat([income_trend, expense_trend])
        
        fig = px.line(
            combined_trend,
            x='date',
            y='amount',
            color='type',
            title="Income vs Expenses Over Time"
        )
        st.plotly_chart(fig)
    
    # Export options
    st.subheader("Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Income Data"):
            csv = export_to_csv(income_df, "income_data.csv")
            st.download_button(
                label="Download Income CSV",
                data=csv,
                file_name="income_data.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Export Expense Data"):
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
