from datetime import date, datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from src.core.models import UserRole, AccountType, RecurrenceType

class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    base_currency: str = Field(default="USD", regex="^[A-Z]{3}$")
    fiscal_year_start: int = Field(default=1, ge=1, le=12)

class CompanyResponse(BaseModel):
    id: int
    name: str
    base_currency: str
    fiscal_year_start: int
    created_at: datetime

class UserCreate(BaseModel):
    email: str = Field(..., regex="^[^@]+@[^@]+\.[^@]+$")
    name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.ANALYST
    company_id: int

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole
    company_id: int
    created_at: datetime

class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    type: AccountType
    company_id: int

class AccountResponse(BaseModel):
    id: int
    name: str
    type: AccountType
    company_id: int

class TransactionCreate(BaseModel):
    date: date
    account_id: int
    category: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=200)
    amount: float
    currency: str = Field(default="USD", regex="^[A-Z]{3}$")
    paid: bool = True
    recurrence: RecurrenceType = RecurrenceType.NONE
    counterpart: Optional[str] = Field(default=None, max_length=100)

class TransactionResponse(BaseModel):
    id: int
    company_id: int
    date: date
    account_id: int
    category: str
    description: str
    amount: float
    currency: str
    paid: bool
    recurrence: RecurrenceType
    counterpart: Optional[str]
    created_at: datetime

class TransactionImport(BaseModel):
    date: str
    category: str
    description: str
    amount: float
    currency: str = "USD"
    account: str
    paid: bool = True

    @validator('date')
    def validate_date(cls, v):
        try:
            return datetime.strptime(v, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(v, '%d/%m/%Y').date()
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD or DD/MM/YYYY format')

class ScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    base: bool = False
    params: Dict[str, Any] = Field(default_factory=dict)

class ScenarioResponse(BaseModel):
    id: int
    company_id: int
    name: str
    base: bool
    params: Dict[str, Any]
    created_at: datetime

class AssumptionCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=50)
    value: float
    scenario_id: Optional[int] = None

class AssumptionResponse(BaseModel):
    id: int
    company_id: int
    key: str
    value: float
    scenario_id: Optional[int]

class CashFlowProjection(BaseModel):
    month: date
    cash_in: float
    cash_out: float
    net_cash: float
    cumulative_cash: float

class KPIMetrics(BaseModel):
    min_cash: float
    min_cash_month: date
    months_of_runway: Optional[int]
    avg_burn_rate: float
    dscr: Optional[float]  # Debt Service Coverage Ratio
    final_cash: float

class ScenarioComparison(BaseModel):
    scenario_name: str
    projections: List[CashFlowProjection]
    kpis: KPIMetrics