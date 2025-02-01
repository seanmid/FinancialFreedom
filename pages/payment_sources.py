import streamlit as st
from database import get_db_connection

def payment_sources_page():
    st.title("Payment Sources Management")
    
    tab1, tab2 = st.tabs(["Add Payment Source", "View Payment Sources"])
    
    with tab1:
        with st.form("add_payment_source_form"):
            name = st.text_input("Payment Source Name")
            source_type = st.selectbox(
                "Type",
                ["credit_card", "bank_account"],
                format_func=lambda x: "Credit Card" if x == "credit_card" else "Bank Account"
            )
            bank_name = st.text_input("Bank Name")
            last_four = st.text_input("Last 4 Digits", max_chars=4)
            
            submitted = st.form_submit_button("Add Payment Source")
            
            if submitted:
                if not name or not bank_name or not last_four or len(last_four) != 4:
                    st.error("Please fill in all fields. Last 4 digits must be exactly 4 characters.")
                elif not last_four.isdigit():
                    st.error("Last 4 digits must be numbers only.")
                else:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    try:
                        cur.execute(
                            """
                            INSERT INTO payment_sources 
                            (name, type, last_four, bank_name, is_active)
                            VALUES (%s, %s, %s, %s, true)
                            """,
                            (name, source_type, last_four, bank_name)
                        )
                        conn.commit()
                        st.success("Payment source added successfully!")
                    except Exception as e:
                        st.error(f"Error adding payment source: {str(e)}")
                    finally:
                        cur.close()
                        conn.close()
    
    with tab2:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT name, type, last_four, bank_name, is_active, created_at
            FROM payment_sources
            ORDER BY created_at DESC
        """)
        
        sources = cur.fetchall()
        
        if sources:
            for source in sources:
                with st.expander(f"{source[0]} ({source[3]} *{source[2]})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Type: {source[1].replace('_', ' ').title()}")
                        st.write(f"Bank: {source[3]}")
                    with col2:
                        st.write(f"Last 4: *{source[2]}")
                        st.write(f"Status: {'Active' if source[4] else 'Inactive'}")
                    st.write(f"Added: {source[5].strftime('%Y-%m-%d')}")
        else:
            st.info("No payment sources found")
        
        cur.close()
        conn.close()

if __name__ == "__main__":
    payment_sources_page()
