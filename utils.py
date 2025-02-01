import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import get_db_connection
from decimal import Decimal

def calculate_monthly_savings(income_total: float, expense_total: float) -> float:
    return income_total - expense_total

def generate_spending_chart(expenses_df: pd.DataFrame):
    fig = px.pie(expenses_df, values='amount', names='category', title='Spending by Category')
    return fig

def generate_trend_chart(transactions_df: pd.DataFrame):
    fig = px.line(transactions_df, x='date', y='amount', title='Spending Trend')
    return fig

def calculate_debt_payoff(principal: float, interest_rate: float, monthly_payment: float) -> dict:
    months = 0
    remaining_balance = principal
    total_interest = 0
    
    while remaining_balance > 0:
        interest = remaining_balance * (interest_rate / 12 / 100)
        total_interest += interest
        
        if monthly_payment > remaining_balance + interest:
            monthly_payment = remaining_balance + interest
            
        principal_payment = monthly_payment - interest
        remaining_balance -= principal_payment
        months += 1
        
        if months > 360:  # 30 years maximum
            break
            
    return {
        'months': months,
        'total_interest': total_interest,
        'total_payment': principal + total_interest
    }

def export_to_csv(data: pd.DataFrame, filename: str):
    return data.to_csv(index=False).encode('utf-8')

def calculate_goal_progress(current_amount: Decimal, target_amount: Decimal) -> float:
    if target_amount == 0:
        return 0.0
    return float(min((current_amount / target_amount) * 100, 100))

def get_category_name(category_id: int) -> str:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM categories WHERE id = %s", (category_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else "Unknown"

def calculate_budget_progress(category_id: int, period: str, user_id: int) -> dict:
    conn = get_db_connection()
    cur = conn.cursor()

    # Get budget amount
    cur.execute(
        "SELECT amount FROM budgets WHERE category_id = %s AND period = %s AND user_id = %s",
        (category_id, period, user_id)
    )
    budget = cur.fetchone()

    if not budget:
        return {'progress': 0, 'remaining': 0}

    budget_amount = float(budget[0])

    # Calculate period dates
    today = datetime.now()
    if period == 'monthly':
        start_date = datetime(today.year, today.month, 1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:  # weekly
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

    # Get spent amount for the specific user
    cur.execute(
        """
        SELECT COALESCE(SUM(amount), 0) 
        FROM expenses 
        WHERE category_id = %s 
        AND date BETWEEN %s AND %s
        AND user_id = %s
        """,
        (category_id, start_date, end_date, user_id)
    )
    spent = float(cur.fetchone()[0])

    cur.close()
    conn.close()

    return {
        'progress': (spent / budget_amount) * 100,
        'remaining': budget_amount - spent
    }
