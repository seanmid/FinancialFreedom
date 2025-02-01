import streamlit as st
from database import get_db_connection
from models import User

def init_auth():
    if 'user' not in st.session_state:
        st.session_state.user = None

def login_user(username: str, password: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, username, password_hash, is_admin, created_at FROM users WHERE username = %s",
            (username,)
        )
        user_data = cur.fetchone()
        
        if user_data and User.verify_password(password, user_data[2]):
            st.session_state.user = User(
                id=user_data[0],
                username=user_data[1],
                is_admin=user_data[3],
                created_at=user_data[4]
            )
            return True
        return False
    finally:
        cur.close()
        conn.close()

def register_user(username: str, password: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if username already exists
        cur.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
        if cur.fetchone()[0] > 0:
            return False
        
        password_hash = User.hash_password(password)
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id, created_at",
            (username, password_hash)
        )
        user_id, created_at = cur.fetchone()
        conn.commit()
        
        st.session_state.user = User(
            id=user_id,
            username=username,
            is_admin=False,
            created_at=created_at
        )
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def logout_user():
    st.session_state.user = None

def require_auth():
    init_auth()
    if not st.session_state.user:
        st.warning("Please log in to access this page")
        st.stop()
    return st.session_state.user

def require_admin():
    user = require_auth()
    if not user.is_admin:
        st.error("Administrator access required")
        st.stop()
    return user
