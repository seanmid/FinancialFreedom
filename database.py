import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
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
        # Create tables if they don't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                type VARCHAR(20) NOT NULL,
                is_custom BOOLEAN DEFAULT false
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id SERIAL PRIMARY KEY,
                description VARCHAR(200) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                frequency VARCHAR(20) NOT NULL,
                category_id INTEGER REFERENCES categories(id),
                date DATE NOT NULL,
                is_recurring BOOLEAN DEFAULT false
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                description VARCHAR(200) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                category_id INTEGER REFERENCES categories(id),
                date DATE NOT NULL,
                payment_method VARCHAR(50),
                necessity_level VARCHAR(20),
                is_recurring BOOLEAN DEFAULT false,
                frequency VARCHAR(20)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id SERIAL PRIMARY KEY,
                category_id INTEGER REFERENCES categories(id),
                amount DECIMAL(10,2) NOT NULL,
                period VARCHAR(20) NOT NULL,
                start_date DATE NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                current_balance DECIMAL(10,2) NOT NULL,
                interest_rate DECIMAL(5,2) NOT NULL,
                minimum_payment DECIMAL(10,2) NOT NULL,
                due_date DATE NOT NULL
            )
        """)

        # Check if categories table is empty before inserting default categories
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