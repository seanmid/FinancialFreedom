import streamlit as st
import plotly.express as px
from database import get_db_connection
from datetime import datetime, date
from decimal import Decimal
from auth import require_auth
from components import add_auth_controls

def goals_page():
    # Ensure user is logged in
    user = require_auth()

    st.title("Financial Goals")

    # Add authentication controls
    add_auth_controls()

    tab1, tab2 = st.tabs(["Set Goals", "Track Progress"])

    with tab1:
        with st.form("add_goal_form"):
            name = st.text_input("Goal Name")
            target_amount = st.number_input("Target Amount ($)", min_value=0.01, step=100.0)
            deadline = st.date_input("Target Date", min_value=date.today())

            # Get expense categories for optional categorization
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name 
                FROM categories 
                WHERE type = 'expense'
                AND (user_id IS NULL OR user_id = %s)
            """, (user.id,))
            categories = cur.fetchall()
            category_options = {cat[1]: cat[0] for cat in categories}
            category_options["None"] = None

            category = st.selectbox(
                "Related Category (Optional)",
                options=list(category_options.keys())
            )

            priority = st.selectbox(
                "Priority",
                ["High", "Medium", "Low"]
            )

            submitted = st.form_submit_button("Set Goal")

            if submitted:
                try:
                    cur.execute(
                        """
                        INSERT INTO financial_goals 
                        (name, target_amount, current_amount, deadline, category_id, 
                         priority, status, created_at, user_id)
                        VALUES (%s, %s, 0, %s, %s, %s, 'in_progress', CURRENT_DATE, %s)
                        """,
                        (name, target_amount, deadline, category_options[category], 
                         priority, user.id)
                    )
                    conn.commit()
                    st.success("Goal set successfully!")
                except Exception as e:
                    st.error(f"Error setting goal: {str(e)}")
                finally:
                    cur.close()
                    conn.close()

    with tab2:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT g.*, c.name as category_name
            FROM financial_goals g
            LEFT JOIN categories c ON g.category_id = c.id
            WHERE g.user_id = %s
            ORDER BY g.deadline
        """, (user.id,))
        goals = cur.fetchall()

        if goals:
            # Summary metrics
            total_target = sum(float(goal[2]) for goal in goals)  # target_amount
            total_current = sum(float(goal[3]) for goal in goals)  # current_amount
            overall_progress = (total_current / total_target * 100) if total_target > 0 else 0

            st.metric(
                "Overall Progress",
                f"${total_current:,.2f} / ${total_target:,.2f}",
                f"{overall_progress:.1f}%"
            )

            # Individual goals
            for goal in goals:
                progress = calculate_goal_progress(goal[3], goal[2])  # current_amount / target_amount
                days_left = (goal[4] - date.today()).days  # deadline - today

                with st.expander(f"{goal[1]} - {goal[6]} Priority"):  # name - priority
                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            "Target Amount",
                            f"${float(goal[2]):,.2f}",
                            f"${float(goal[3]):,.2f} saved"
                        )
                        if goal[5]:  # category_id
                            st.write(f"Category: {goal[8]}")  # category_name

                    with col2:
                        st.metric(
                            "Time Remaining",
                            f"{days_left} days",
                            f"Due: {goal[4]}"
                        )

                    # Progress bar
                    progress_color = "normal"
                    if progress >= 90:
                        progress_color = "off"
                    elif progress >= 75:
                        progress_color = "warning"

                    st.progress(min(progress / 100, 1.0), text=f"{progress:.1f}%")

                    # Update current amount
                    new_amount = st.number_input(
                        "Update Current Amount",
                        min_value=0.0,
                        value=float(goal[3]),
                        key=f"update_amount_{goal[0]}"
                    )

                    if st.button("Update Progress", key=f"update_goal_{goal[0]}"):
                        try:
                            cur.execute(
                                """
                                UPDATE financial_goals 
                                SET current_amount = %s,
                                    status = CASE 
                                        WHEN %s >= target_amount THEN 'completed'
                                        ELSE 'in_progress'
                                    END
                                WHERE id = %s AND user_id = %s
                                """,
                                (new_amount, new_amount, goal[0], user.id)
                            )
                            conn.commit()
                            st.success("Progress updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating progress: {str(e)}")
        else:
            st.info("No financial goals set yet")

        cur.close()
        conn.close()

if __name__ == "__main__":
    goals_page()