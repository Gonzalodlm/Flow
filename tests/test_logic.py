import pytest
from datetime import date, datetime
from sqlmodel import Session, create_engine, SQLModel
from src.core.models import Company, Account, Transaction, Scenario, Assumption, AccountType, DEFAULT_ASSUMPTIONS
from src.core.logic import CashFlowEngine
from src.core.db import get_session

@pytest.fixture
def test_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session

@pytest.fixture
def test_company(test_session):
    """Create a test company."""
    company = Company(
        name="Test Company",
        base_currency="USD",
        fiscal_year_start=1
    )
    test_session.add(company)
    test_session.commit()
    test_session.refresh(company)
    return company

@pytest.fixture
def test_accounts(test_session, test_company):
    """Create test accounts."""
    accounts = [
        Account(name="Revenue", type=AccountType.OPERATING, company_id=test_company.id),
        Account(name="COGS", type=AccountType.OPERATING, company_id=test_company.id),
        Account(name="OpEx", type=AccountType.OPERATING, company_id=test_company.id),
        Account(name="Equipment", type=AccountType.INVESTING, company_id=test_company.id),
    ]
    
    for account in accounts:
        test_session.add(account)
    
    test_session.commit()
    
    for account in accounts:
        test_session.refresh(account)
    
    return accounts

@pytest.fixture
def test_transactions(test_session, test_company, test_accounts):
    """Create test transactions."""
    revenue_account = next(a for a in test_accounts if a.name == "Revenue")
    cogs_account = next(a for a in test_accounts if a.name == "COGS")
    opex_account = next(a for a in test_accounts if a.name == "OpEx")
    
    transactions = [
        # January
        Transaction(
            company_id=test_company.id,
            date=date(2024, 1, 15),
            account_id=revenue_account.id,
            category="Sales",
            description="Revenue",
            amount=10000.0,
            currency="USD",
            paid=True
        ),
        Transaction(
            company_id=test_company.id,
            date=date(2024, 1, 20),
            account_id=cogs_account.id,
            category="COGS",
            description="Cost of sales",
            amount=-3000.0,
            currency="USD",
            paid=True
        ),
        Transaction(
            company_id=test_company.id,
            date=date(2024, 1, 30),
            account_id=opex_account.id,
            category="Salary",
            description="Salaries",
            amount=-2000.0,
            currency="USD",
            paid=True
        ),
        # February
        Transaction(
            company_id=test_company.id,
            date=date(2024, 2, 15),
            account_id=revenue_account.id,
            category="Sales",
            description="Revenue",
            amount=11000.0,
            currency="USD",
            paid=True
        ),
        Transaction(
            company_id=test_company.id,
            date=date(2024, 2, 20),
            account_id=cogs_account.id,
            category="COGS",
            description="Cost of sales",
            amount=-3300.0,
            currency="USD",
            paid=True
        ),
    ]
    
    for transaction in transactions:
        test_session.add(transaction)
    
    test_session.commit()
    return transactions

@pytest.fixture
def test_scenario(test_session, test_company):
    """Create a test scenario with assumptions."""
    scenario = Scenario(
        name="Test Scenario",
        base=True,
        company_id=test_company.id,
        params={}
    )
    test_session.add(scenario)
    test_session.commit()
    test_session.refresh(scenario)
    
    # Add assumptions
    for key, value in DEFAULT_ASSUMPTIONS.items():
        assumption = Assumption(
            company_id=test_company.id,
            scenario_id=scenario.id,
            key=key,
            value=value
        )
        test_session.add(assumption)
    
    test_session.commit()
    return scenario

def test_cash_flow_engine_initialization(test_session, test_company):
    """Test CashFlowEngine initialization."""
    engine = CashFlowEngine(test_session, test_company.id)
    assert engine.company_id == test_company.id
    assert engine.session == test_session

def test_get_assumptions(test_session, test_company, test_scenario):
    """Test getting assumptions."""
    engine = CashFlowEngine(test_session, test_company.id)
    assumptions = engine.get_assumptions(test_scenario.id)
    
    # Should contain all default assumptions
    for key in DEFAULT_ASSUMPTIONS:
        assert key in assumptions
    
    # Should have correct values
    assert assumptions['sales_growth'] == DEFAULT_ASSUMPTIONS['sales_growth']
    assert assumptions['dso_days'] == DEFAULT_ASSUMPTIONS['dso_days']

def test_historical_averages(test_session, test_company, test_accounts, test_transactions):
    """Test calculation of historical averages."""
    engine = CashFlowEngine(test_session, test_company.id)
    averages = engine.calculate_historical_averages()
    
    # Should return positive revenue
    assert averages['monthly_revenue'] > 0
    
    # Should return negative COGS and OpEx
    assert averages['monthly_cogs'] <= 0
    assert averages['monthly_opex'] <= 0

def test_cash_flow_projection(test_session, test_company, test_accounts, test_transactions, test_scenario):
    """Test cash flow projection calculation."""
    engine = CashFlowEngine(test_session, test_company.id)
    projections = engine.project_cash_flow(test_scenario.id, months=12)
    
    # Should return 12 projections
    assert len(projections) == 12
    
    # Each projection should have required fields
    for projection in projections:
        assert hasattr(projection, 'month')
        assert hasattr(projection, 'cash_in')
        assert hasattr(projection, 'cash_out')
        assert hasattr(projection, 'net_cash')
        assert hasattr(projection, 'cumulative_cash')
        
        # Cash out should be positive (absolute value)
        assert projection.cash_out >= 0

def test_kpi_calculation(test_session, test_company, test_accounts, test_transactions, test_scenario):
    """Test KPI calculation."""
    engine = CashFlowEngine(test_session, test_company.id)
    projections = engine.project_cash_flow(test_scenario.id, months=12)
    kpis = engine.calculate_kpis(projections)
    
    # Should have all required KPIs
    assert hasattr(kpis, 'min_cash')
    assert hasattr(kpis, 'min_cash_month')
    assert hasattr(kpis, 'final_cash')
    assert hasattr(kpis, 'avg_burn_rate')
    
    # Min cash month should be a date
    assert isinstance(kpis.min_cash_month, date)
    
    # Final cash should be from last projection
    assert kpis.final_cash == projections[-1].cumulative_cash

def test_scenario_comparison(test_session, test_company, test_accounts, test_transactions, test_scenario):
    """Test scenario comparison."""
    # Create a second scenario
    scenario2 = Scenario(
        name="Optimistic Scenario",
        base=False,
        company_id=test_company.id,
        params={}
    )
    test_session.add(scenario2)
    test_session.commit()
    test_session.refresh(scenario2)
    
    # Add different assumptions for scenario2
    optimistic_assumptions = DEFAULT_ASSUMPTIONS.copy()
    optimistic_assumptions['sales_growth'] = 0.10  # Higher growth
    
    for key, value in optimistic_assumptions.items():
        assumption = Assumption(
            company_id=test_company.id,
            scenario_id=scenario2.id,
            key=key,
            value=value
        )
        test_session.add(assumption)
    
    test_session.commit()
    
    # Test comparison
    engine = CashFlowEngine(test_session, test_company.id)
    comparisons = engine.create_scenario_comparison([test_scenario.id, scenario2.id])
    
    # Should have 2 scenarios
    assert len(comparisons) == 2
    
    # Each comparison should have required fields
    for comparison in comparisons:
        assert 'scenario_name' in comparison
        assert 'projections' in comparison
        assert 'kpis' in comparison

def test_current_cash_position(test_session, test_company, test_accounts, test_transactions):
    """Test current cash position calculation."""
    engine = CashFlowEngine(test_session, test_company.id)
    current_cash = engine._get_current_cash_position()
    
    # Should be positive (revenue > expenses in test data)
    assert current_cash >= 0
    
    # Should equal sum of all transaction amounts
    expected_cash = sum(tx.amount for tx in test_transactions if tx.paid)
    assert current_cash == max(expected_cash, 0.0)

def test_cash_inflow_calculation(test_session, test_company):
    """Test cash inflow calculation with DSO."""
    engine = CashFlowEngine(test_session, test_company.id)
    
    # Test first month (should have partial collection)
    cash_in_month_0 = engine._calculate_cash_inflows(10000, 30, 0)
    assert cash_in_month_0 > 0
    assert cash_in_month_0 < 10000  # Should be less than full revenue due to DSO
    
    # Test later month (should have full collection)
    cash_in_month_2 = engine._calculate_cash_inflows(10000, 30, 2)
    assert cash_in_month_2 == 10000

def test_debt_service_calculation(test_session, test_company):
    """Test debt service calculation."""
    engine = CashFlowEngine(test_session, test_company.id)
    
    assumptions = {
        'debt_principal': 60000.0,
        'interest_rate': 0.12,
        'debt_term_months': 60
    }
    
    # Calculate monthly payment
    debt_service = engine._calculate_debt_service(assumptions, 0)
    
    # Should be positive
    assert debt_service > 0
    
    # Should be reasonable monthly payment
    assert debt_service < assumptions['debt_principal'] / 12  # Less than principal/12

def test_tax_payment_calculation(test_session, test_company):
    """Test tax payment calculation."""
    engine = CashFlowEngine(test_session, test_company.id)
    
    # Quarter end date
    quarter_end = date(2024, 3, 31)
    
    # Should calculate tax payment
    tax_payment = engine._calculate_tax_payment(10000, 0.22, quarter_end)
    assert tax_payment > 0
    
    # Non-quarter end date
    non_quarter_end = date(2024, 2, 15)
    tax_payment_zero = engine._calculate_tax_payment(10000, 0.22, non_quarter_end)
    assert tax_payment_zero == 0

if __name__ == "__main__":
    pytest.main([__file__])