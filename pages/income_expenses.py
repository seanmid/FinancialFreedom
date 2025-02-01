import streamlit as st
from database import get_db_connection
from datetime import datetime
from decimal import Decimal
import pandas as pd

def income_expenses_page():
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

            # Get categories based on transaction type
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name FROM categories WHERE type = %s",
                (transaction_type.lower(),)
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
                    ORDER BY name
                """)
                payment_sources = cur.fetchall()
                payment_source_options = {
                    f"{src[1]} ({src[2].replace('_', ' ').title()} - {src[3]} *{src[4]})": src[0] 
                    for src in payment_sources
                }

                payment_source = st.selectbox(
                    "Payment Source",
                    options=list(payment_source_options.keys())
                )

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
                            (description, amount, frequency, category_id, date, is_recurring)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (description, amount, frequency, category_options[category],
                             date, is_recurring)
                        )
                    else:
                        cur.execute(
                            """
                            INSERT INTO expenses 
                            (description, amount, category_id, payment_source_id, date,
                             necessity_level, is_recurring, frequency)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (description, amount, category_options[category],
                             payment_source_options[payment_source], date,
                             necessity_level, is_recurring, frequency)
                        )

                    conn.commit()
                    st.success("Transaction added successfully!")
                except Exception as e:
                    st.error(f"Error adding transaction: {str(e)}")
                finally:
                    cur.close()
                    conn.close()

    with tab2:
        # View transactions
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
                ORDER BY date DESC
                """
            )
            columns = ['ID', 'Description', 'Amount', 'Category', 'Date', 
                      'Frequency', 'Is Recurring']
        else:
            cur.execute(
                """
                SELECT e.id, e.description, e.amount, c.name as category,
                       ps.name as source_name, ps.bank_name, ps.last_four,
                       e.date, e.necessity_level, e.is_recurring, e.frequency
                FROM expenses e
                JOIN categories c ON e.category_id = c.id
                LEFT JOIN payment_sources ps ON e.payment_source_id = ps.id
                ORDER BY date DESC
                """
            )
            columns = ['ID', 'Description', 'Amount', 'Category', 'Payment Source',
                      'Date', 'Necessity Level', 'Is Recurring', 'Frequency']

        transactions = cur.fetchall()

        if transactions:
            df = pd.DataFrame(transactions)

            if view_type == "Expenses":
                # Format payment source display
                df['Payment Source'] = df.apply(
                    lambda x: f"{x['source_name']} ({x['bank_name']} *{x['last_four']})"
                    if pd.notna(x['source_name']) else "N/A",
                    axis=1
                )
                # Reorder columns for display
                display_df = df[[0, 1, 2, 3, 'Payment Source', 7, 8, 9, 10]]
            else:
                display_df = df

            # Rename columns for display
            display_df.columns = columns

            # Add delete buttons
            for idx, row in display_df.iterrows():
                with st.expander(f"{row['Description']} - ${float(row['Amount']):,.2f}"):
                    st.write(display_df.iloc[idx])
                    if st.button("Delete", key=f"delete_{view_type.lower()}_{row['ID']}", type="secondary"):
                        if st.button("Confirm Delete", key=f"confirm_delete_{view_type.lower()}_{row['ID']}", type="primary"):
                            try:
                                table = "income" if view_type == "Income" else "expenses"
                                cur.execute(f"DELETE FROM {table} WHERE id = %s", (row['ID'],))
                                conn.commit()
                                st.success(f"{view_type} entry deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting entry: {str(e)}")

        else:
            st.info(f"No {view_type.lower()} transactions found")

        cur.close()
        conn.close()

if __name__ == "__main__":
    income_expenses_page()