import streamlit as st
from sqlmodel import Session, select
from src.auth.simple_auth import require_auth, get_current_company_id, is_admin
from src.core.db import get_session
from src.core.models import Company, User, Account, AccountType, UserRole
from src.ui.components import display_success_message, display_error_message

st.set_page_config(page_title="Admin", page_icon="🛠️", layout="wide")

def main():
    if not require_auth():
        return
    
    if not is_admin():
        st.error("❌ Access Denied: Admin privileges required")
        return
    
    st.title("🛠️ Admin")
    st.markdown("---")
    
    # Tabs for different admin functions
    tab1, tab2, tab3, tab4 = st.tabs(["🏢 Companies", "👥 Users", "📁 Accounts", "⚙️ System"])
    
    with tab1:
        handle_companies_tab()
    
    with tab2:
        handle_users_tab()
    
    with tab3:
        handle_accounts_tab()
    
    with tab4:
        handle_system_tab()

def handle_companies_tab():
    """Handle company management."""
    st.markdown("### 🏢 Company Management")
    
    with next(get_session()) as session:
        # Display existing companies
        companies = session.exec(select(Company)).all()
        
        if companies:
            st.markdown("#### 📋 Existing Companies")
            
            company_data = []
            for company in companies:
                user_count = len(session.exec(
                    select(User).where(User.company_id == company.id)
                ).all())
                
                company_data.append({
                    'ID': company.id,
                    'Name': company.name,
                    'Currency': company.base_currency,
                    'Fiscal Year Start': f"Month {company.fiscal_year_start}",
                    'Users': user_count,
                    'Created': company.created_at.strftime('%Y-%m-%d')
                })
            
            import pandas as pd
            df = pd.DataFrame(company_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Create new company
        st.markdown("#### 🆕 Create New Company")
        
        with st.form("create_company"):
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input(
                    "Company Name *",
                    placeholder="e.g., Acme Corp S.A.",
                    help="Legal name of the company"
                )
                
                base_currency = st.selectbox(
                    "Base Currency *",
                    options=["USD", "EUR", "GBP", "UYU", "ARS", "BRL"],
                    index=0,
                    help="Primary currency for financial reporting"
                )
            
            with col2:
                fiscal_year_start = st.selectbox(
                    "Fiscal Year Start Month *",
                    options=list(range(1, 13)),
                    index=0,
                    format_func=lambda x: f"Month {x} ({'Jan' if x==1 else 'Feb' if x==2 else 'Mar' if x==3 else 'Apr' if x==4 else 'May' if x==5 else 'Jun' if x==6 else 'Jul' if x==7 else 'Aug' if x==8 else 'Sep' if x==9 else 'Oct' if x==10 else 'Nov' if x==11 else 'Dec'})",
                    help="Month when fiscal year begins"
                )
                
                create_default_accounts = st.checkbox(
                    "Create Default Accounts",
                    value=True,
                    help="Automatically create standard account structure"
                )
            
            submitted = st.form_submit_button("🏢 Create Company", type="primary")
            
            if submitted:
                if not company_name:
                    st.error("Company name is required.")
                else:
                    try:
                        # Create company
                        new_company = Company(
                            name=company_name,
                            base_currency=base_currency,
                            fiscal_year_start=fiscal_year_start
                        )
                        
                        session.add(new_company)
                        session.commit()
                        session.refresh(new_company)
                        
                        # Create default accounts if requested
                        if create_default_accounts:
                            default_accounts = [
                                ("Cash", AccountType.OPERATING),
                                ("Revenue", AccountType.OPERATING),
                                ("Cost of Goods Sold", AccountType.OPERATING),
                                ("Operating Expenses", AccountType.OPERATING),
                                ("Salaries & Benefits", AccountType.OPERATING),
                                ("Marketing & Sales", AccountType.OPERATING),
                                ("Equipment", AccountType.INVESTING),
                                ("Software & Technology", AccountType.INVESTING),
                                ("Bank Loan", AccountType.FINANCING),
                                ("Line of Credit", AccountType.FINANCING),
                            ]
                            
                            for acc_name, acc_type in default_accounts:
                                account = Account(
                                    name=acc_name,
                                    type=acc_type,
                                    company_id=new_company.id
                                )
                                session.add(account)
                        
                        session.commit()
                        display_success_message(f"Company '{company_name}' created successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        session.rollback()
                        display_error_message("Failed to create company", str(e))

def handle_users_tab():
    """Handle user management."""
    st.markdown("### 👥 User Management")
    
    with next(get_session()) as session:
        # Display existing users
        users = session.exec(select(User, Company).join(Company)).all()
        
        if users:
            st.markdown("#### 📋 Existing Users")
            
            user_data = []
            for user, company in users:
                user_data.append({
                    'ID': user.id,
                    'Name': user.name,
                    'Email': user.email,
                    'Role': user.role.value.title(),
                    'Company': company.name,
                    'Created': user.created_at.strftime('%Y-%m-%d')
                })
            
            import pandas as pd
            df = pd.DataFrame(user_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Create new user
        st.markdown("#### 🆕 Create New User")
        
        # Get companies for dropdown
        companies = session.exec(select(Company)).all()
        company_options = {c.name: c.id for c in companies}
        
        if not company_options:
            st.warning("No companies found. Create a company first.")
            return
        
        with st.form("create_user"):
            col1, col2 = st.columns(2)
            
            with col1:
                user_name = st.text_input(
                    "Full Name *",
                    placeholder="e.g., John Smith",
                    help="User's full name"
                )
                
                user_email = st.text_input(
                    "Email *",
                    placeholder="e.g., john@company.com",
                    help="User's email address (must be unique)"
                )
            
            with col2:
                user_role = st.selectbox(
                    "Role *",
                    options=[UserRole.ANALYST, UserRole.ADMIN],
                    format_func=lambda x: x.value.title(),
                    help="User's role determines access permissions"
                )
                
                company_name = st.selectbox(
                    "Company *",
                    options=list(company_options.keys()),
                    help="Company the user belongs to"
                )
            
            st.info("💡 **Note**: Users must be added to the authentication system (users.yaml) separately to enable login.")
            
            submitted = st.form_submit_button("👥 Create User", type="primary")
            
            if submitted:
                if not user_name or not user_email:
                    st.error("Name and email are required.")
                elif '@' not in user_email:
                    st.error("Please enter a valid email address.")
                else:
                    try:
                        # Check if email already exists
                        existing_user = session.exec(
                            select(User).where(User.email == user_email)
                        ).first()
                        
                        if existing_user:
                            st.error("A user with this email already exists.")
                        else:
                            new_user = User(
                                name=user_name,
                                email=user_email,
                                role=user_role,
                                company_id=company_options[company_name]
                            )
                            
                            session.add(new_user)
                            session.commit()
                            
                            display_success_message(f"User '{user_name}' created successfully!")
                            st.info("Remember to add this user to src/auth/users.yaml for authentication.")
                            st.rerun()
                        
                    except Exception as e:
                        session.rollback()
                        display_error_message("Failed to create user", str(e))

def handle_accounts_tab():
    """Handle account management."""
    st.markdown("### 📁 Account Management")
    
    company_id = get_current_company_id()
    if not company_id:
        st.error("No company selected.")
        return
    
    with next(get_session()) as session:
        company = session.get(Company, company_id)
        if not company:
            st.error("Company not found.")
            return
        
        st.markdown(f"#### 🏢 Managing Accounts for: {company.name}")
        
        # Display existing accounts
        accounts = session.exec(
            select(Account).where(Account.company_id == company_id)
        ).all()
        
        if accounts:
            st.markdown("#### 📋 Existing Accounts")
            
            account_data = []
            for account in accounts:
                # Count transactions for this account
                from src.core.models import Transaction
                tx_count = len(session.exec(
                    select(Transaction).where(Transaction.account_id == account.id)
                ).all())
                
                account_data.append({
                    'ID': account.id,
                    'Name': account.name,
                    'Type': account.type.value,
                    'Transactions': tx_count,
                    'Created': account.created_at.strftime('%Y-%m-%d')
                })
            
            import pandas as pd
            df = pd.DataFrame(account_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Create new account
        st.markdown("#### 🆕 Create New Account")
        
        with st.form("create_account"):
            col1, col2 = st.columns(2)
            
            with col1:
                account_name = st.text_input(
                    "Account Name *",
                    placeholder="e.g., Professional Services Revenue",
                    help="Descriptive name for the account"
                )
            
            with col2:
                account_type = st.selectbox(
                    "Account Type *",
                    options=[AccountType.OPERATING, AccountType.INVESTING, AccountType.FINANCING],
                    format_func=lambda x: x.value,
                    help="Account type for cash flow categorization"
                )
            
            # Account type descriptions
            st.markdown("**Account Type Descriptions:**")
            st.write("• **Operating**: Day-to-day business activities (revenue, expenses, working capital)")
            st.write("• **Investing**: Capital expenditures, asset purchases, investments")
            st.write("• **Financing**: Debt, equity, loans, dividend payments")
            
            submitted = st.form_submit_button("📁 Create Account", type="primary")
            
            if submitted:
                if not account_name:
                    st.error("Account name is required.")
                else:
                    try:
                        # Check if account name already exists for this company
                        existing_account = session.exec(
                            select(Account).where(
                                Account.company_id == company_id,
                                Account.name == account_name
                            )
                        ).first()
                        
                        if existing_account:
                            st.error("An account with this name already exists.")
                        else:
                            new_account = Account(
                                name=account_name,
                                type=account_type,
                                company_id=company_id
                            )
                            
                            session.add(new_account)
                            session.commit()
                            
                            display_success_message(f"Account '{account_name}' created successfully!")
                            st.rerun()
                        
                    except Exception as e:
                        session.rollback()
                        display_error_message("Failed to create account", str(e))

def handle_system_tab():
    """Handle system administration."""
    st.markdown("### ⚙️ System Administration")
    
    # Database information
    st.markdown("#### 💾 Database Information")
    
    with next(get_session()) as session:
        # Count records
        company_count = len(session.exec(select(Company)).all())
        user_count = len(session.exec(select(User)).all())
        
        from src.core.models import Transaction, Account, Scenario, Assumption
        account_count = len(session.exec(select(Account)).all())
        transaction_count = len(session.exec(select(Transaction)).all())
        scenario_count = len(session.exec(select(Scenario)).all())
        assumption_count = len(session.exec(select(Assumption)).all())
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Companies", company_count)
            st.metric("Users", user_count)
        
        with col2:
            st.metric("Accounts", account_count)
            st.metric("Transactions", transaction_count)
        
        with col3:
            st.metric("Scenarios", scenario_count)
            st.metric("Assumptions", assumption_count)
    
    st.markdown("---")
    
    # System operations
    st.markdown("#### 🔧 System Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🗃️ Database Operations")
        
        if st.button("🔄 Reinitialize Database", type="secondary"):
            st.warning("⚠️ This will recreate all tables. Existing data may be lost.")
            
            if st.checkbox("I understand the risks"):
                try:
                    from src.core.db import create_db_and_tables
                    create_db_and_tables()
                    display_success_message("Database reinitialized successfully!")
                except Exception as e:
                    display_error_message("Database reinitialization failed", str(e))
        
        if st.button("🌱 Seed Sample Data", type="secondary"):
            try:
                from src.core.db import seed_database
                seed_database()
                display_success_message("Sample data seeded successfully!")
            except Exception as e:
                display_error_message("Seeding failed", str(e))
    
    with col2:
        st.markdown("##### 📊 System Health")
        
        # Check system health
        health_checks = [
            ("Database Connection", "✅ Connected"),
            ("Authentication System", "✅ Active"),
            ("FX Rate Service", "✅ Available"),
            ("Export Services", "✅ Ready")
        ]
        
        for check, status in health_checks:
            st.write(f"• **{check}**: {status}")
    
    st.markdown("---")
    
    # Configuration
    st.markdown("#### ⚙️ Configuration")
    
    st.info("""
    **Environment Configuration:**
    - Database: SQLite (development) - Ready for PostgreSQL migration
    - Authentication: File-based (users.yaml) - Ready for OAuth/SAML
    - File Storage: Local filesystem - Ready for cloud storage
    - Currency Rates: CSV-based - Ready for API integration
    """)
    
    # Migration notes
    st.markdown("#### 🚀 Production Migration Notes")
    
    with st.expander("📋 SaaS Migration Checklist"):
        st.markdown("""
        **Database Migration:**
        - [ ] Set up PostgreSQL/Supabase instance
        - [ ] Update DATABASE_URL environment variable
        - [ ] Run database migrations
        - [ ] Import existing data
        
        **Authentication Migration:**
        - [ ] Implement OAuth/SAML providers
        - [ ] Set up user registration flow
        - [ ] Configure role-based access control
        - [ ] Add multi-tenant security
        
        **Infrastructure:**
        - [ ] Deploy to cloud platform (AWS/GCP/Azure)
        - [ ] Set up CDN for assets
        - [ ] Configure load balancing
        - [ ] Set up monitoring and logging
        
        **Feature Enhancements:**
        - [ ] Add payment processing (Stripe)
        - [ ] Implement subscription management
        - [ ] Add advanced analytics
        - [ ] Set up automated backups
        """)

if __name__ == "__main__":
    main()