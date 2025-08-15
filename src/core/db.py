import os
import sys
import streamlit as st
from typing import Generator, Optional
from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy.engine import Engine
from datetime import datetime, date
from src.core.models import (
    Company, User, Account, Transaction, Scenario, Assumption,
    UserRole, AccountType, RecurrenceType, DEFAULT_ASSUMPTIONS
)

# Try to get DATABASE_URL from Streamlit secrets first, then environment variables
try:
    DATABASE_URL = st.secrets["general"]["DATABASE_URL"]
except:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/cashflow.db")

def get_engine() -> Engine:
    """Get database engine with proper configuration."""
    if DATABASE_URL.startswith("sqlite"):
        # Ensure data directory exists for SQLite
        import pathlib
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if "./" in db_path:
            data_dir = pathlib.Path(db_path).parent
            data_dir.mkdir(parents=True, exist_ok=True)
        
        connect_args = {"check_same_thread": False}
        engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
    else:
        # PostgreSQL or other databases
        engine = create_engine(DATABASE_URL, echo=False)
    return engine

def create_db_and_tables():
    """Create database and all tables."""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Get database session."""
    engine = get_engine()
    with Session(engine) as session:
        yield session

def init_database():
    """Initialize database with tables."""
    create_db_and_tables()
    print("Database initialized successfully.")

def seed_database():
    """Seed database with sample data."""
    engine = get_engine()
    
    with Session(engine) as session:
        # Check if data already exists
        existing_company = session.exec(select(Company)).first()
        if existing_company:
            print("Database already seeded.")
            return
        
        # Create sample company
        company = Company(
            name="Demo Company S.A.",
            base_currency="USD",
            fiscal_year_start=1
        )
        session.add(company)
        session.commit()
        session.refresh(company)
        
        # Create sample users
        admin_user = User(
            email="admin@demo.com",
            name="Admin User",
            role=UserRole.ADMIN,
            company_id=company.id
        )
        analyst_user = User(
            email="analyst@demo.com",
            name="Financial Analyst",
            role=UserRole.ANALYST,
            company_id=company.id
        )
        session.add(admin_user)
        session.add(analyst_user)
        
        # Create sample accounts
        accounts_data = [
            ("Revenue", AccountType.OPERATING),
            ("Cost of Goods Sold", AccountType.OPERATING),
            ("Operating Expenses", AccountType.OPERATING),
            ("Salaries", AccountType.OPERATING),
            ("Marketing", AccountType.OPERATING),
            ("Equipment", AccountType.INVESTING),
            ("Loan", AccountType.FINANCING),
            ("Cash", AccountType.OPERATING),
        ]
        
        accounts = []
        for name, acc_type in accounts_data:
            account = Account(
                name=name,
                type=acc_type,
                company_id=company.id
            )
            accounts.append(account)
            session.add(account)
        
        session.commit()
        
        # Refresh accounts to get IDs
        for account in accounts:
            session.refresh(account)
        
        # Create base scenario
        base_scenario = Scenario(
            name="Base Case",
            base=True,
            company_id=company.id,
            params={}
        )
        session.add(base_scenario)
        session.commit()
        session.refresh(base_scenario)
        
        # Create default assumptions
        for key, value in DEFAULT_ASSUMPTIONS.items():
            assumption = Assumption(
                key=key,
                value=value,
                company_id=company.id,
                scenario_id=base_scenario.id
            )
            session.add(assumption)
        
        # Create sample transactions
        revenue_account = next(a for a in accounts if a.name == "Revenue")
        cogs_account = next(a for a in accounts if a.name == "Cost of Goods Sold")
        opex_account = next(a for a in accounts if a.name == "Operating Expenses")
        salary_account = next(a for a in accounts if a.name == "Salaries")
        
        sample_transactions = [
            # Revenue transactions (positive amounts)
            Transaction(
                company_id=company.id,
                date=date(2024, 1, 15),
                account_id=revenue_account.id,
                category="Sales",
                description="Q1 Sales Revenue",
                amount=50000.0,
                currency="USD",
                paid=True
            ),
            Transaction(
                company_id=company.id,
                date=date(2024, 2, 15),
                account_id=revenue_account.id,
                category="Sales",
                description="Q1 Sales Revenue",
                amount=52000.0,
                currency="USD",
                paid=True
            ),
            Transaction(
                company_id=company.id,
                date=date(2024, 3, 15),
                account_id=revenue_account.id,
                category="Sales",
                description="Q1 Sales Revenue",
                amount=48000.0,
                currency="USD",
                paid=True
            ),
            # Expense transactions (negative amounts)
            Transaction(
                company_id=company.id,
                date=date(2024, 1, 5),
                account_id=cogs_account.id,
                category="COGS",
                description="Cost of Goods Sold",
                amount=-20000.0,
                currency="USD",
                paid=True
            ),
            Transaction(
                company_id=company.id,
                date=date(2024, 1, 30),
                account_id=salary_account.id,
                category="Payroll",
                description="Monthly Salaries",
                amount=-15000.0,
                currency="USD",
                paid=True,
                recurrence=RecurrenceType.MONTHLY
            ),
            Transaction(
                company_id=company.id,
                date=date(2024, 1, 10),
                account_id=opex_account.id,
                category="Rent",
                description="Office Rent",
                amount=-3000.0,
                currency="USD",
                paid=True,
                recurrence=RecurrenceType.MONTHLY
            ),
        ]
        
        for transaction in sample_transactions:
            session.add(transaction)
        
        session.commit()
        print("Database seeded successfully.")

def get_company_by_id(session: Session, company_id: int) -> Optional[Company]:
    """Get company by ID."""
    return session.get(Company, company_id)

def get_user_by_email(session: Session, email: str) -> Optional[User]:
    """Get user by email."""
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def get_companies_for_user(session: Session, user_id: int) -> list[Company]:
    """Get all companies a user has access to."""
    statement = select(Company).join(User).where(User.id == user_id)
    return list(session.exec(statement))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if "--init" in sys.argv:
            init_database()
        if "--seed" in sys.argv:
            seed_database()
    else:
        print("Usage: python -m src.core.db [--init] [--seed]")
        print("  --init: Initialize database and create tables")
        print("  --seed: Seed database with sample data")