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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                type VARCHAR(20) NOT NULL,
                is_custom BOOLEAN DEFAULT false
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS payment_sources (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                type VARCHAR(20) NOT NULL,  -- 'bank_account' or 'credit_card'
                last_four VARCHAR(4),
                bank_name VARCHAR(100),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
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
                payment_source_id INTEGER REFERENCES payment_sources(id),
                date DATE NOT NULL,
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
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS financial_goals (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                target_amount DECIMAL(10,2) NOT NULL,
                current_amount DECIMAL(10,2) DEFAULT 0,
                deadline DATE NOT NULL,
                category_id INTEGER REFERENCES categories(id),
                priority VARCHAR(20) NOT NULL,
                status VARCHAR(20) DEFAULT 'in_progress',
                created_at DATE DEFAULT CURRENT_DATE
            )
        """)

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

        cur.execute("SELECT COUNT(*) FROM payment_sources")
        count = cur.fetchone()
        if count is not None and count[0] == 0:
            default_payment_sources = [
                ('Chase Freedom', 'credit_card', '1234', 'Chase', True),
                ('Bank of America Checking', 'bank_account', '5678', 'Bank of America', True),
                ('Wells Fargo Savings', 'bank_account', '9012', 'Wells Fargo', True)
            ]

            cur.executemany(
                """
                INSERT INTO payment_sources (name, type, last_four, bank_name, is_active)
                VALUES (%s, %s, %s, %s, %s)
                """,
                default_payment_sources
            )

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()