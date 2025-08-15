from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import calendar
from dateutil.relativedelta import relativedelta

def get_month_start(target_date: date) -> date:
    """Get the first day of the month for a given date."""
    return date(target_date.year, target_date.month, 1)

def get_month_end(target_date: date) -> date:
    """Get the last day of the month for a given date."""
    last_day = calendar.monthrange(target_date.year, target_date.month)[1]
    return date(target_date.year, target_date.month, last_day)

def get_months_range(start_date: date, num_months: int) -> List[date]:
    """Generate a list of month start dates."""
    months = []
    current = get_month_start(start_date)
    
    for i in range(num_months):
        months.append(current)
        current = current + relativedelta(months=1)
    
    return months

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency string."""
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "EUR":
        return f"€{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator

def calculate_working_capital_days(
    revenue_monthly: float,
    cogs_monthly: float,
    dso_days: float,
    dpo_days: float,
    inventory_days: float = 0
) -> Dict[str, float]:
    """Calculate working capital components in days."""
    days_in_month = 30
    
    # Accounts Receivable = (DSO / 30) * Monthly Revenue
    accounts_receivable = (dso_days / days_in_month) * revenue_monthly
    
    # Accounts Payable = (DPO / 30) * Monthly COGS
    accounts_payable = (dpo_days / days_in_month) * abs(cogs_monthly)
    
    # Inventory = (Inventory Days / 30) * Monthly COGS
    inventory = (inventory_days / days_in_month) * abs(cogs_monthly)
    
    # Net Working Capital = AR + Inventory - AP
    net_working_capital = accounts_receivable + inventory - accounts_payable
    
    return {
        "accounts_receivable": accounts_receivable,
        "accounts_payable": accounts_payable,
        "inventory": inventory,
        "net_working_capital": net_working_capital
    }

def apply_growth_rate(base_amount: float, growth_rate: float, periods: int) -> float:
    """Apply compound growth rate over periods."""
    return base_amount * ((1 + growth_rate) ** periods)

def get_quarter_from_date(target_date: date) -> int:
    """Get quarter number (1-4) from date."""
    return (target_date.month - 1) // 3 + 1

def is_quarter_end(target_date: date) -> bool:
    """Check if date is end of quarter."""
    return target_date.month in [3, 6, 9, 12] and target_date == get_month_end(target_date)

def validate_percentage(value: float, field_name: str) -> float:
    """Validate that a value is a reasonable percentage."""
    if not -1.0 <= value <= 2.0:  # Allow -100% to 200%
        raise ValueError(f"{field_name} must be between -100% and 200%")
    return value

def validate_positive(value: float, field_name: str) -> float:
    """Validate that a value is positive."""
    if value < 0:
        raise ValueError(f"{field_name} must be positive")
    return value

def parse_currency_input(input_str: str) -> float:
    """Parse currency input string to float."""
    # Remove currency symbols and commas
    cleaned = input_str.replace("$", "").replace("€", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        raise ValueError(f"Invalid currency format: {input_str}")

def generate_recurrent_dates(
    start_date: date,
    recurrence: str,
    end_date: date
) -> List[date]:
    """Generate list of dates for recurrent transactions."""
    dates = []
    current = start_date
    
    while current <= end_date:
        dates.append(current)
        
        if recurrence == "weekly":
            current += timedelta(weeks=1)
        elif recurrence == "monthly":
            current += relativedelta(months=1)
        elif recurrence == "quarterly":
            current += relativedelta(months=3)
        else:
            break  # No recurrence
    
    return dates