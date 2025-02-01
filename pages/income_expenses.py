import streamlit as st
from database import get_db_connection
from datetime import datetime
from decimal import Decimal

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
                payment_method = st.selectbox(
                    "Payment Method",
                    ["Cash", "Credit Card", "Debit Card", "Bank Transfer"]
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
                            (description, amount, category_id, date, payment_method,
                             necessity_level, is_recurring, frequency)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (description, amount, category_options[category], date,
                             payment_method, necessity_level, is_recurring, frequency)
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
                SELECT i.*, c.name as category_name
                FROM income i
                JOIN categories c ON i.category_id = c.id
                ORDER BY date DESC
                """
            )
        else:
            cur.execute(
                """
                SELECT e.*, c.name as category_name
                FROM expenses e
                JOIN categories c ON e.category_id = c.id
                ORDER BY date DESC
                """
            )
        
        transactions = cur.fetchall()
        
        if transactions:
            # Convert to DataFrame for display
            import pandas as pd
            columns = ['ID', 'Description', 'Amount', 'Category', 'Date']
            if view_type == "Income":
                columns.extend(['Frequency', 'Is Recurring'])
            else:
                columns.extend(['Payment Method', 'Necessity Level', 'Is Recurring', 'Frequency'])
            
            df = pd.DataFrame(transactions)
            st.dataframe(df, use_container_width=True)
        else:
            st.info(f"No {view_type.lower()} transactions found")
        
        cur.close()
        conn.close()

if __name__ == "__main__":
    income_expenses_page()
