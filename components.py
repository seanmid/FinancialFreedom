import streamlit as st
from auth import logout_user
from database import get_db_connection
from models import User

def add_auth_controls():
    """Add authentication controls (logout button and password update) to the sidebar"""
    with st.sidebar:
        if st.button("Logout"):
            logout_user()
            st.rerun()
            
        st.write("---")
        with st.expander("Update Password"):
            with st.form("update_password_form"):
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("Update Password"):
                    if new_password != confirm_password:
                        st.error("New passwords do not match")
                    elif not current_password:
                        st.error("Please enter your current password")
                    else:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        try:
                            # Verify current password
                            cur.execute(
                                "SELECT password_hash FROM users WHERE id = %s",
                                (st.session_state.user.id,)
                            )
                            current_hash = cur.fetchone()[0]
                            
                            if User.verify_password(current_password, current_hash):
                                # Update password
                                new_password_hash = User.hash_password(new_password)
                                cur.execute(
                                    "UPDATE users SET password_hash = %s WHERE id = %s",
                                    (new_password_hash, st.session_state.user.id)
                                )
                                conn.commit()
                                st.success("Password updated successfully!")
                            else:
                                st.error("Current password is incorrect")
                        except Exception as e:
                            st.error(f"Error updating password: {str(e)}")
                        finally:
                            cur.close()
                            conn.close()
