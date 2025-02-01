import os
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
from urllib.parse import urlparse

def get_db_connection():
    # Try to get DATABASE_URL first (for Streamlit.io deployment)
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # Parse the URL
        parsed = urlparse(database_url)
        return psycopg2.connect(
            host=parsed.hostname,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password,
            port=parsed.port or 5432
        )
    else:
        # Fallback to individual credentials (for local development)
        return psycopg2.connect(
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            port=os.environ['PGPORT']
        )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Add users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add user_id foreign key to existing tables
        cur.execute("""
            ALTER TABLE categories
            ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)
        """)

        cur.execute("""
            ALTER TABLE payment_sources
            ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)
        """)

        cur.execute("""
            ALTER TABLE income
            ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)
        """)

        cur.execute("""
            ALTER TABLE expenses
            ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)
        """)

        cur.execute("""
            ALTER TABLE budgets
            ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)
        """)

        cur.execute("""
            ALTER TABLE debts
            ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)
        """)

        cur.execute("""
            ALTER TABLE financial_goals
            ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)
        """)

        # Check if admin user exists
        cur.execute("SELECT COUNT(*) FROM users WHERE is_admin = true")
        count = cur.fetchone()
        if count is not None and count[0] == 0:
            # Create default admin user
            admin_password = "admin123"  # This should be changed after first login
            password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
            cur.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, true)",
                ("admin", password_hash.decode('utf-8'))
            )

        # Add default categories if none exist
        cur.execute("SELECT COUNT(*) FROM categories")
        count = cur.fetchone()
        if count is not None and count[0] == 0:
            default_categories = [
                ('Salary', 'income', False),
                ('Bonus', 'income', False),
                ('Freelance', 'income', False),
                ('Housing', 'expense', False),
                ('Transportation', 'expense', False),
                ('Groceries', 'expense', False),
                ('Healthcare', 'expense', False),
                ('Entertainment', 'expense', False),
                ('Education', 'expense', False)
            ]

            cur.executemany(
                "INSERT INTO categories (name, type, is_custom) VALUES (%s, %s, %s)",
                default_categories
            )

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()