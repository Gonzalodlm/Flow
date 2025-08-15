from datetime import datetime, date
from typing import Optional, Dict, Any
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
import json

class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"

class AccountType(str, Enum):
    OPERATING = "Operating"
    INVESTING = "Investing"
    FINANCING = "Financing"

class RecurrenceType(str, Enum):
    NONE = "none"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

class Company(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    base_currency: str = Field(default="USD")
    fiscal_year_start: int = Field(default=1)  # Month 1-12
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    users: list["User"] = Relationship(back_populates="company")
    accounts: list["Account"] = Relationship(back_populates="company")
    transactions: list["Transaction"] = Relationship(back_populates="company")
    scenarios: list["Scenario"] = Relationship(back_populates="company")
    assumptions: list["Assumption"] = Relationship(back_populates="company")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    role: UserRole = Field(default=UserRole.ANALYST)
    company_id: int = Field(foreign_key="company.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    company: Company = Relationship(back_populates="users")

class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    type: AccountType
    company_id: int = Field(foreign_key="company.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    company: Company = Relationship(back_populates="accounts")
    transactions: list["Transaction"] = Relationship(back_populates="account")

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    date: date = Field(index=True)
    account_id: int = Field(foreign_key="account.id")
    category: str = Field(index=True)
    description: str
    amount: float  # Signed amount (positive = inflow, negative = outflow)
    currency: str = Field(default="USD")
    paid: bool = Field(default=True)
    recurrence: RecurrenceType = Field(default=RecurrenceType.NONE)
    counterpart: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    company: Company = Relationship(back_populates="transactions")
    account: Account = Relationship(back_populates="transactions")

class Scenario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    name: str = Field(index=True)
    base: bool = Field(default=False)
    params: str = Field(default="{}")  # Store JSON as string for better compatibility
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    company: Company = Relationship(back_populates="scenarios")
    assumptions: list["Assumption"] = Relationship(back_populates="scenario")
    
    def get_params(self) -> Dict[str, Any]:
        """Get params as dictionary."""
        try:
            return json.loads(self.params)
        except:
            return {}
    
    def set_params(self, params: Dict[str, Any]):
        """Set params from dictionary."""
        self.params = json.dumps(params)

class Assumption(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    key: str = Field(index=True)
    value: float
    scenario_id: Optional[int] = Field(foreign_key="scenario.id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    company: Company = Relationship(back_populates="assumptions")
    scenario: Optional[Scenario] = Relationship(back_populates="assumptions")

# Default assumptions keys
DEFAULT_ASSUMPTIONS = {
    "sales_growth": 0.05,  # 5% monthly
    "dso_days": 30,        # Days Sales Outstanding
    "dpo_days": 30,        # Days Payable Outstanding
    "inventory_days": 15,
    "tax_rate": 0.22,      # 22%
    "capex_monthly": 0.0,  # Monthly CapEx
    "interest_rate": 0.12, # Annual interest rate
    "min_cash_target": 10000.0,
    "debt_principal": 0.0,
    "debt_term_months": 60,
    "opex_growth": 0.02,   # 2% monthly operating expense growth
}