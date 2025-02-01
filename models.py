from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional
import bcrypt

@dataclass
class User:
    username: str
    is_admin: bool = False
    created_at: Optional[date] = None
    id: Optional[int] = None

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

@dataclass
class Income:
    description: str
    amount: Decimal
    frequency: str
    category_id: int
    date: date
    is_recurring: bool
    user_id: Optional[int] = None
    id: Optional[int] = None

@dataclass
class Expense:
    description: str
    amount: Decimal
    category_id: int
    date: date
    payment_method: str
    necessity_level: str
    is_recurring: bool
    frequency: Optional[str]
    user_id: Optional[int] = None
    id: Optional[int] = None

@dataclass
class Budget:
    category_id: int
    amount: Decimal
    period: str
    start_date: date
    user_id: Optional[int] = None
    id: Optional[int] = None

@dataclass
class Debt:
    name: str
    total_amount: Decimal
    current_balance: Decimal
    interest_rate: Decimal
    minimum_payment: Decimal
    due_date: date
    user_id: Optional[int] = None
    id: Optional[int] = None

@dataclass
class Category:
    name: str
    type: str
    is_custom: bool
    user_id: Optional[int] = None
    id: Optional[int] = None

@dataclass
class FinancialGoal:
    name: str
    target_amount: Decimal
    current_amount: Decimal
    deadline: date
    category_id: Optional[int]
    priority: str
    status: str
    created_at: date
    user_id: Optional[int] = None
    id: Optional[int] = None