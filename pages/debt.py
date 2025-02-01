import streamlit as st
import plotly.express as px
from database import get_db_connection
from utils import calculate_debt_payoff
from datetime import datetime
from auth import require_auth

def debt_page():
    # Ensure user is logged in
    user = require_auth()

    st.title("Debt Management")

    tab1, tab2, tab3 = st.tabs(["Add Debt", "Debt Overview", "Payoff Calculator"])

    with tab1:
        with st.form("add_debt_form"):
            name = st.text_input("Debt Name")
            total_amount = st.number_input("Total Amount", min_value=0.01, step=0.01)
            current_balance = st.number_input("Current Balance", min_value=0.01, step=0.01)
            interest_rate = st.number_input("Interest Rate (%)", min_value=0.01, step=0.01)
            minimum_payment = st.number_input("Minimum Payment", min_value=0.01, step=0.01)
            due_date = st.date_input("Due Date")

            submitted = st.form_submit_button("Add Debt")

            if submitted:
                conn = get_db_connection()
                cur = conn.cursor()

                try:
                    cur.execute(
                        """
                        INSERT INTO debts 
                        (name, total_amount, current_balance, interest_rate,
                         minimum_payment, due_date, user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (name, total_amount, current_balance, interest_rate,
                         minimum_payment, due_date, user.id)
                    )
                    conn.commit()
                    st.success("Debt added successfully!")
                except Exception as e:
                    st.error(f"Error adding debt: {str(e)}")
                finally:
                    cur.close()
                    conn.close()

    with tab2:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT * FROM debts 
            WHERE user_id = %s
            ORDER BY due_date
            """, 
            (user.id,)
        )
        debts = cur.fetchall()

        if debts:
            total_debt = sum(debt[3] for debt in debts)  # Sum of current balances
            st.metric("Total Debt", f"${total_debt:,.2f}")

            # Create pie chart of debt distribution
            debt_data = {
                'names': [debt[1] for debt in debts],
                'values': [float(debt[3]) for debt in debts]
            }
            fig = px.pie(
                values=debt_data['values'],
                names=debt_data['names'],
                title="Debt Distribution"
            )
            st.plotly_chart(fig)

            # List all debts
            for debt in debts:
                with st.expander(f"{debt[1]} - ${float(debt[3]):,.2f}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Total Amount: ${float(debt[2]):,.2f}")
                        st.write(f"Interest Rate: {float(debt[4])}%")
                    with col2:
                        st.write(f"Minimum Payment: ${float(debt[5]):,.2f}")
                        st.write(f"Due Date: {debt[6]}")
        else:
            st.info("No debts recorded")

        cur.close()
        conn.close()

    with tab3:
        st.subheader("Debt Payoff Calculator")

        col1, col2 = st.columns(2)

        with col1:
            principal = st.number_input("Debt Amount", min_value=0.01, step=100.0)
            interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.01, step=0.1)

        with col2:
            monthly_payment = st.number_input("Monthly Payment", min_value=0.01, step=50.0)

        if st.button("Calculate Payoff Plan"):
            payoff_results = calculate_debt_payoff(principal, interest_rate, monthly_payment)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Time to Pay Off", f"{payoff_results['months']} months")
            with col2:
                st.metric("Total Interest", f"${payoff_results['total_interest']:,.2f}")
            with col3:
                st.metric("Total Payment", f"${payoff_results['total_payment']:,.2f}")

if __name__ == "__main__":
    debt_page()