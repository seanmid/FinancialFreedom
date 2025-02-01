import streamlit as st
from database import get_db_connection
from datetime import datetime
from decimal import Decimal
import pandas as pd
from auth import require_auth

def income_expenses_page():
    # Ensure user is logged in
    user = require_auth()

    st.title("Income & Expenses Management")

    tab1, tab2 = st.tabs(["Add Transaction", "View Transactions"])

    with tab1:
        # Transaction type selection
        transaction_type = st.radio(
            "Transaction Type",
            ["Income", "Expense"],
            horizontal=True
        )

        with st.form(f"add_{transaction_type.lower()}_form"):
            description = st.text_input("Description")
            amount = st.number_input("Amount", min_value=0.01, step=0.01)
            date = st.date_input("Date")

            # Get categories based on transaction type and user
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, name 
                FROM categories 
                WHERE type = %s 
                AND (user_id IS NULL OR user_id = %s)
                """,
                (transaction_type.lower(), user.id)
            )
            categories = cur.fetchall()
            category_options = {cat[1]: cat[0] for cat in categories}

            category = st.selectbox(
                "Category",
                options=list(category_options.keys())
            )

            if transaction_type == "Income":
                frequency = st.selectbox(
                    "Frequency",
                    ["One-time", "Weekly", "Monthly", "Annually"]
                )
            else:
                frequency = st.selectbox(
                    "Frequency",
                    ["One-time", "Weekly", "Monthly", "Annually"]
                )

                # Get payment sources for expenses
                cur.execute("""
                    SELECT id, name, type, bank_name, last_four 
                    FROM payment_sources 
                    WHERE is_active = true
                    AND user_id = %s
                    ORDER BY name
                """, (user.id,))
                payment_sources = cur.fetchall()
                payment_source_options = {
                    f"{src[1]} ({src[2].replace('_', ' ').title()} - {src[3]} *{src[4]})": src[0] 
                    for src in payment_sources
                }

                if payment_sources:
                    payment_source = st.selectbox(
                        "Payment Source",
                        options=list(payment_source_options.keys())
                    )
                else:
                    st.warning("Please add a payment source first")
                    st.stop()

                necessity_level = st.selectbox(
                    "Necessity Level",
                    ["Essential", "Important", "Optional"]
                )

            is_recurring = st.checkbox("Is this a recurring transaction?")

            submitted = st.form_submit_button("Add Transaction")

            if submitted:
                try:
                    if transaction_type == "Income":
                        cur.execute(
                            """
                            INSERT INTO income 
                            (description, amount, frequency, category_id, date, 
                             is_recurring, user_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (description, amount, frequency, category_options[category],
                             date, is_recurring, user.id)
                        )
                    else:
                        cur.execute(
                            """
                            INSERT INTO expenses 
                            (description, amount, category_id, payment_source_id, date,
                             necessity_level, is_recurring, frequency, user_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (description, amount, category_options[category],
                             payment_source_options[payment_source], date,
                             necessity_level, is_recurring, frequency, user.id)
                        )

                    conn.commit()
                    st.success("Transaction added successfully!")
                except Exception as e:
                    st.error(f"Error adding transaction: {str(e)}")
                finally:
                    cur.close()
                    conn.close()

    with tab2:
        view_type = st.radio(
            "View",
            ["Income", "Expenses"],
            horizontal=True
        )

        conn = get_db_connection()
        cur = conn.cursor()

        if view_type == "Income":
            cur.execute(
                """
                SELECT i.id, i.description, i.amount, c.name as category,
                       i.date, i.frequency, i.is_recurring
                FROM income i
                JOIN categories c ON i.category_id = c.id
                WHERE i.user_id = %s
                ORDER BY date DESC
                """,
                (user.id,)
            )
            columns = ['ID', 'Description', 'Amount', 'Category', 'Date', 
                      'Frequency', 'Is Recurring']
        else:
            cur.execute(
                """
                SELECT e.id, e.description, e.amount, c.name as category,
                       ps.name, ps.bank_name, ps.last_four,
                       e.date, e.necessity_level, e.is_recurring, e.frequency
                FROM expenses e
                JOIN categories c ON e.category_id = c.id
                LEFT JOIN payment_sources ps ON e.payment_source_id = ps.id
                WHERE e.user_id = %s
                ORDER BY date DESC
                """,
                (user.id,)
            )
            columns = ['ID', 'Description', 'Amount', 'Category', 
                      'Source Name', 'Bank Name', 'Last Four',
                      'Date', 'Necessity Level', 'Is Recurring', 'Frequency']

        transactions = cur.fetchall()

        if transactions:
            # Create DataFrame with named columns immediately
            df = pd.DataFrame(transactions, columns=columns)

            if view_type == "Expenses":
                # Format payment source display using proper column names
                df['Payment Source'] = df.apply(
                    lambda x: f"{x['Source Name']} ({x['Bank Name']} *{x['Last Four']})"
                    if pd.notna(x['Source Name']) else "N/A",
                    axis=1
                )

                # Select and reorder columns for display
                display_columns = ['ID', 'Description', 'Amount', 'Category', 
                                 'Payment Source', 'Date', 'Necessity Level', 
                                 'Is Recurring', 'Frequency']
                display_df = df[display_columns]
            else:
                display_df = df

            # Initialize deletion state in session state
            if 'delete_id' not in st.session_state:
                st.session_state.delete_id = None

            # Add delete buttons
            for idx, row in display_df.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{row['Description']} - ${float(row['Amount']):,.2f}")
                    if st.session_state.delete_id == row['ID']:
                        confirm_col1, confirm_col2 = st.columns(2)
                        with confirm_col1:
                            if st.button("✓ Confirm", key=f"confirm_{row['ID']}"):
                                try:
                                    table = "income" if view_type == "Income" else "expenses"
                                    cur.execute(
                                        f"DELETE FROM {table} WHERE id = %s AND user_id = %s", 
                                        (row['ID'], user.id)
                                    )
                                    conn.commit()
                                    st.success(f"{view_type} entry deleted!")
                                    st.session_state.delete_id = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting entry: {str(e)}")
                        with confirm_col2:
                            if st.button("✗ Cancel", key=f"cancel_{row['ID']}"):
                                st.session_state.delete_id = None
                                st.rerun()
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{row['ID']}"):
                        st.session_state.delete_id = row['ID']
                        st.rerun()
                st.write("---")

        else:
            st.info(f"No {view_type.lower()} transactions found")

        cur.close()
        conn.close()

if __name__ == "__main__":
    income_expenses_page()