import streamlit as st
import plotly.express as px
from database import get_db_connection
from utils import calculate_budget_progress
from datetime import datetime
from auth import require_auth
from components import add_auth_controls

def budget_page():
    # Ensure user is logged in
    user = require_auth()
    if not user:
        st.stop()  # Stop execution if user is not logged in

    st.title("Budget Management")

    # Add authentication controls
    add_auth_controls()

    tab1, tab2 = st.tabs(["Budget Setup", "Budget Overview"])

    with tab1:
        with st.form("budget_setup_form"):
            # Get expense categories
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, name 
                FROM categories 
                WHERE type = 'expense'
                AND (user_id IS NULL OR user_id = %s)
                """,
                (user.id,)
            )
            categories = cur.fetchall()
            category_options = {cat[1]: cat[0] for cat in categories}

            category = st.selectbox(
                "Category",
                options=list(category_options.keys())
            )

            amount = st.number_input("Budget Amount", min_value=0.01, step=0.01)
            period = st.selectbox(
                "Budget Period",
                ["weekly", "monthly"]
            )
            start_date = st.date_input("Start Date")

            submitted = st.form_submit_button("Set Budget")

            if submitted:
                try:
                    cur.execute(
                        """
                        INSERT INTO budgets (category_id, amount, period, start_date, user_id)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (category_id, period, user_id) 
                        DO UPDATE SET amount = %s, start_date = %s
                        """,
                        (category_options[category], amount, period, start_date, user.id,
                         amount, start_date)
                    )
                    conn.commit()
                    st.success("Budget set successfully!")
                except Exception as e:
                    st.error(f"Error setting budget: {str(e)}")
                finally:
                    cur.close()
                    conn.close()

    with tab2:
        # Budget progress overview
        st.subheader("Budget Progress")

        conn = get_db_connection()
        cur = conn.cursor()

        # Get all budgets for the current user
        cur.execute(
            """
            SELECT b.*, c.name as category_name
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            WHERE b.user_id = %s
            """,
            (user.id,)
        )
        budgets = cur.fetchall()

        if budgets:
            for budget in budgets:
                progress = calculate_budget_progress(budget[1], budget[3], user.id)

                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        f"{budget[-1]} ({budget[3]})",
                        f"${float(budget[2]):,.2f}",
                        f"${progress['remaining']:,.2f} remaining"
                    )

                with col2:
                    progress_color = "normal"
                    if progress['progress'] >= 90:
                        progress_color = "off"
                    elif progress['progress'] >= 75:
                        progress_color = "warning"

                    st.progress(min(progress['progress'] / 100, 1.0), text=f"{progress['progress']:.1f}%")

                st.divider()
        else:
            st.info("No budgets set yet")

        cur.close()
        conn.close()

if __name__ == "__main__":
    budget_page()