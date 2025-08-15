import streamlit as st
from src.auth.auth import require_auth, setup_sidebar

# Auto-initialize database on first run
@st.cache_resource
def init_database_if_needed():
    """Initialize database if it doesn't exist."""
    try:
        from src.core.db import init_database, seed_database, get_session
        from src.core.models import Company
        from sqlmodel import select
        
        # Check if database exists and has data
        with next(get_session()) as session:
            companies = session.exec(select(Company)).first()
            if not companies:
                # Database exists but no data, seed it
                seed_database()
                st.success("✅ Database initialized with sample data!")
    except Exception as e:
        # Database doesn't exist, create it
        try:
            from src.core.db import init_database, seed_database
            init_database()
            seed_database()
            st.success("✅ Database created and initialized!")
        except Exception as init_error:
            st.error(f"❌ Database initialization failed: {init_error}")

# Initialize database
init_database_if_needed()

# Configure page
st.set_page_config(
    page_title="Cash Flow Analytics",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point."""
    # Require authentication
    if not require_auth():
        return
    
    # Setup sidebar with user info
    setup_sidebar()
    
    # Main content
    st.title("💰 Cash Flow Analytics")
    st.markdown("---")
    
    # Welcome message
    user_name = st.session_state.get('name', 'User')
    st.markdown(f"""
    ### Welcome back, {user_name}! 👋
    
    Use the sidebar to navigate between different features:
    
    - **🏠 Dashboard**: Overview of your cash flow and key metrics
    - **📥 Transactions**: Import and manage financial transactions
    - **⚙️ Assumptions**: Configure business drivers and assumptions
    - **📈 Projections**: View detailed 24-month cash flow projections
    - **🧪 Scenarios**: Create and compare different business scenarios
    - **📊 Reports**: Generate Excel and PDF reports
    - **🛠️ Admin**: Manage companies and users (admin only)
    
    ### Quick Stats
    """)
    
    # Quick stats in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📅 Current Month", "Dec 2024")
    
    with col2:
        st.metric("🏢 Active Company", f"ID: {st.session_state.get('company_id', 'N/A')}")
    
    with col3:
        st.metric("👤 Your Role", st.session_state.get('user_role', 'Unknown').title())
    
    with col4:
        st.metric("📊 Data Status", "Ready")
    
    st.markdown("---")
    
    # Quick navigation buttons
    st.markdown("### Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 View Dashboard", use_container_width=True):
            st.switch_page("src/ui/pages/1_🏠_Dashboard.py")
    
    with col2:
        if st.button("📥 Import Data", use_container_width=True):
            st.switch_page("src/ui/pages/2_📥_Transacciones.py")
    
    with col3:
        if st.button("📈 View Projections", use_container_width=True):
            st.switch_page("src/ui/pages/4_📈_Proyecciones.py")
    
    # Information section
    st.markdown("---")
    st.markdown("""
    ### 📚 Getting Started
    
    1. **Import your financial data** by going to the Transactions page
    2. **Review and adjust assumptions** in the Assumptions & Drivers page
    3. **Generate cash flow projections** to see your 24-month outlook
    4. **Create scenarios** to model different business conditions
    5. **Export reports** for sharing with stakeholders
    
    ### 💡 Tips
    - Import historical transactions for more accurate projections
    - Regularly update your assumptions based on actual performance
    - Use scenarios to prepare for different market conditions
    - Export reports monthly for board meetings and investor updates
    """)

if __name__ == "__main__":
    main()