from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

@dataclass
class Income:
    description: str
    amount: Decimal
    frequency: str
    category_id: int
    date: date
    is_recurring: bool
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
    id: Optional[int] = None

@dataclass
class Budget:
    category_id: int
    amount: Decimal
    period: str
    start_date: date
    id: Optional[int] = None

@dataclass
class Debt:
    name: str
    total_amount: Decimal
    current_balance: Decimal
    interest_rate: Decimal
    minimum_payment: Decimal
    due_date: date
    id: Optional[int] = None

@dataclass
class Category:
    name: str
    type: str
    is_custom: bool
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
    id: Optional[int] = None