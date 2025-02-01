import streamlit as st
from database import get_db_connection
from auth import require_auth
from components import add_auth_controls

def payment_sources_page():
    # Ensure user is logged in
    user = require_auth()

    st.title("Payment Sources Management")

    # Add authentication controls
    add_auth_controls()

    tab1, tab2 = st.tabs(["Add Payment Source", "View Payment Sources"])

    with tab1:
        with st.form("add_payment_source_form"):
            name = st.text_input("Payment Source Name")
            source_type = st.selectbox(
                "Type",
                ["credit_card", "debit_card", "bank_account"],
                format_func=lambda x: {
                    "credit_card": "Credit Card",
                    "debit_card": "Debit Card",
                    "bank_account": "Bank Account"
                }[x]
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
                            (name, type, last_four, bank_name, is_active, user_id)
                            VALUES (%s, %s, %s, %s, true, %s)
                            """,
                            (name, source_type, last_four, bank_name, user.id)
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
            SELECT id, name, type, last_four, bank_name, is_active, created_at,
                   (SELECT COUNT(*) FROM expenses WHERE payment_source_id = payment_sources.id) as usage_count
            FROM payment_sources
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user.id,))

        sources = cur.fetchall()

        if sources:
            for source in sources:
                source_id, name, type_, last_four, bank_name, is_active, created_at, usage_count = source

                with st.expander(f"{name} ({bank_name} *{last_four})"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(f"Type: {type_.replace('_', ' ').title()}")
                        st.write(f"Bank: {bank_name}")
                    with col2:
                        st.write(f"Last 4: *{last_four}")
                        st.write(f"Status: {'Active' if is_active else 'Inactive'}")
                    with col3:
                        if is_active:
                            if st.button(f"Deactivate", key=f"deactivate_{source_id}"):
                                try:
                                    cur.execute(
                                        """
                                        UPDATE payment_sources 
                                        SET is_active = false 
                                        WHERE id = %s AND user_id = %s
                                        """,
                                        (source_id, user.id)
                                    )
                                    conn.commit()
                                    st.success("Payment source deactivated!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deactivating payment source: {str(e)}")
                        else:
                            col3a, col3b = st.columns(2)
                            with col3a:
                                if st.button(f"Reactivate", key=f"reactivate_{source_id}"):
                                    try:
                                        cur.execute(
                                            """
                                            UPDATE payment_sources 
                                            SET is_active = true 
                                            WHERE id = %s AND user_id = %s
                                            """,
                                            (source_id, user.id)
                                        )
                                        conn.commit()
                                        st.success("Payment source reactivated!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error reactivating payment source: {str(e)}")
                            with col3b:
                                if usage_count == 0:
                                    if st.button("Delete", key=f"delete_{source_id}"):
                                        try:
                                            cur.execute(
                                                """
                                                DELETE FROM payment_sources 
                                                WHERE id = %s AND user_id = %s AND 
                                                      NOT EXISTS (
                                                          SELECT 1 
                                                          FROM expenses 
                                                          WHERE payment_source_id = %s
                                                      )
                                                """,
                                                (source_id, user.id, source_id)
                                            )
                                            conn.commit()
                                            st.success("Payment source deleted!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error deleting payment source: {str(e)}")

                    st.write(f"Added: {created_at.strftime('%Y-%m-%d')}")
                    st.write(f"Times used: {usage_count}")
        else:
            st.info("No payment sources found")

        cur.close()
        conn.close()

if __name__ == "__main__":
    payment_sources_page()