import streamlit as st
import plotly.express as px
from database import get_db_connection
from utils import calculate_debt_payoff
from datetime import datetime
from auth import require_auth
from components import add_auth_controls

def debt_page():
    # Ensure user is logged in
    user = require_auth()
    if not user:
        st.stop()  # Stop execution if user is not logged in

    st.title("Debt Management")

    # Add authentication controls
    add_auth_controls()

    tab1, tab2, tab3 = st.tabs(["Add Debt", "Debt Overview", "Payoff Calculator"])

    with tab1:
        with st.form("add_debt_form"):
            name = st.text_input("Debt Name")
            total_amount = st.number_input("Total Amount", min_value=0.01, step=0.01)
            current_balance = st.number_input("Current Balance", min_value=0.01, step=0.01)
            interest_rate = st.number_input("Interest Rate (%)", min_value=0.01, step=0.1)
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

            # List all debts with edit and delete options
            for debt in debts:
                debt_id = debt[0]
                with st.expander(f"{debt[1]} - ${float(debt[3]):,.2f}"):
                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        st.write(f"Total Amount: ${float(debt[2]):,.2f}")
                        st.write(f"Interest Rate: {float(debt[4])}%")
                    with col2:
                        st.write(f"Minimum Payment: ${float(debt[5]):,.2f}")
                        st.write(f"Due Date: {debt[6]}")
                    with col3:
                        # Edit button
                        if st.button("✏️ Edit", key=f"edit_{debt_id}"):
                            st.session_state[f'editing_debt_{debt_id}'] = True

                        # Delete button
                        if st.button("🗑️ Delete", key=f"delete_{debt_id}"):
                            st.session_state[f'confirm_delete_debt_{debt_id}'] = True

                    # Edit form
                    if st.session_state.get(f'editing_debt_{debt_id}', False):
                        with st.form(key=f"edit_debt_form_{debt_id}"):
                            new_name = st.text_input("Name", value=debt[1])
                            new_total = st.number_input("Total Amount", value=float(debt[2]), min_value=0.01)
                            new_balance = st.number_input("Current Balance", value=float(debt[3]), min_value=0.01)
                            new_rate = st.number_input("Interest Rate (%)", value=float(debt[4]), min_value=0.01)
                            new_payment = st.number_input("Minimum Payment", value=float(debt[5]), min_value=0.01)
                            new_due_date = st.date_input("Due Date", value=debt[6])

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Save Changes"):
                                    try:
                                        cur.execute("""
                                            UPDATE debts 
                                            SET name = %s, total_amount = %s, current_balance = %s,
                                                interest_rate = %s, minimum_payment = %s, due_date = %s
                                            WHERE id = %s AND user_id = %s
                                        """, (new_name, new_total, new_balance, new_rate, 
                                              new_payment, new_due_date, debt_id, user.id))
                                        conn.commit()
                                        st.success("Debt updated successfully!")
                                        st.session_state[f'editing_debt_{debt_id}'] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating debt: {str(e)}")
                            with col2:
                                if st.form_submit_button("Cancel"):
                                    st.session_state[f'editing_debt_{debt_id}'] = False
                                    st.rerun()

                    # Delete confirmation
                    if st.session_state.get(f'confirm_delete_debt_{debt_id}', False):
                        st.warning("Are you sure you want to delete this debt?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✓ Yes", key=f"confirm_yes_{debt_id}"):
                                try:
                                    cur.execute(
                                        "DELETE FROM debts WHERE id = %s AND user_id = %s",
                                        (debt_id, user.id)
                                    )
                                    conn.commit()
                                    st.success("Debt deleted successfully!")
                                    st.session_state[f'confirm_delete_debt_{debt_id}'] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting debt: {str(e)}")
                        with col2:
                            if st.button("✗ No", key=f"confirm_no_{debt_id}"):
                                st.session_state[f'confirm_delete_debt_{debt_id}'] = False
                                st.rerun()
        else:
            st.info("No debts recorded")

        cur.close()
        conn.close()

    with tab3:
        st.subheader("Debt Payoff Calculator")

        # Option to select existing debt or enter custom values
        use_existing = st.checkbox("Use existing debt")

        if use_existing:
            # Get existing debts for selection
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, name, current_balance, interest_rate, minimum_payment
                FROM debts
                WHERE user_id = %s
                ORDER BY name
                """,
                (user.id,)
            )
            existing_debts = cur.fetchall()
            cur.close()
            conn.close()

            if existing_debts:
                debt_options = {f"{debt[1]} (${float(debt[2]):,.2f})": debt for debt in existing_debts}
                selected_debt_name = st.selectbox(
                    "Select Debt",
                    options=list(debt_options.keys())
                )
                selected_debt = debt_options[selected_debt_name]

                principal = float(selected_debt[2])  # current_balance
                interest_rate = float(selected_debt[3])
                monthly_payment = float(selected_debt[4])

                # Allow overriding monthly payment
                monthly_payment = st.number_input(
                    "Monthly Payment",
                    min_value=float(selected_debt[4]),
                    value=float(selected_debt[4]),
                    step=50.0
                )
            else:
                st.info("No existing debts found")
                use_existing = False

        if not use_existing:
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