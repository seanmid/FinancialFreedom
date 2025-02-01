import streamlit as st
from database import get_db_connection
from auth import require_admin
from models import User
from components import add_auth_controls

def user_management_page():
    # Ensure only admin can access this page
    user = require_admin()

    st.title("User Management")

    # Add authentication controls
    add_auth_controls()

    # Get all users
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, username, is_admin, created_at 
        FROM users 
        ORDER BY created_at DESC
    """)
    users = cur.fetchall()

    if users:
        for user_data in users:
            user_id, username, is_admin, created_at = user_data

            with st.expander(f"User: {username}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"Created: {created_at.strftime('%Y-%m-%d')}")
                    st.write(f"Role: {'Administrator' if is_admin else 'User'}")

                    # Add password update section
                    with st.expander("Update Password"):
                        with st.form(key=f"update_password_form_{user_id}"):
                            new_password = st.text_input("New Password", type="password")
                            confirm_password = st.text_input("Confirm Password", type="password")

                            if st.form_submit_button("Update Password"):
                                if new_password != confirm_password:
                                    st.error("Passwords do not match")
                                else:
                                    try:
                                        password_hash = User.hash_password(new_password)
                                        cur.execute(
                                            "UPDATE users SET password_hash = %s WHERE id = %s",
                                            (password_hash, user_id)
                                        )
                                        conn.commit()
                                        st.success("Password updated successfully!")
                                    except Exception as e:
                                        st.error(f"Error updating password: {str(e)}")

                with col2:
                    if user_id != user.id:  # Prevent admin from deleting themselves
                        if st.button("Delete User", key=f"delete_{user_id}"):
                            try:
                                # First, delete all user's data
                                tables = ['income', 'expenses', 'budgets', 'debts', 
                                        'payment_sources', 'financial_goals']
                                for table in tables:
                                    cur.execute(f"DELETE FROM {table} WHERE user_id = %s", 
                                              (user_id,))

                                # Then delete the user
                                cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
                                conn.commit()
                                st.success(f"User {username} deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting user: {str(e)}")

                        # Add button to toggle admin status
                        if st.button(
                            "Remove Admin" if is_admin else "Make Admin",
                            key=f"admin_{user_id}"
                        ):
                            try:
                                cur.execute(
                                    "UPDATE users SET is_admin = NOT is_admin WHERE id = %s",
                                    (user_id,)
                                )
                                conn.commit()
                                st.success(f"Updated admin status for {username}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating admin status: {str(e)}")
                    else:
                        st.info("Cannot modify your own account")
    else:
        st.info("No users found")

    cur.close()
    conn.close()

if __name__ == "__main__":
    user_management_page()