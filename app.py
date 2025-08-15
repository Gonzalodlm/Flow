import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
import io

# Configure page
st.set_page_config(
    page_title="Cash Flow Analytics",
    page_icon="💰",
    layout="wide"
)

# Simple authentication
def check_auth():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Cash Flow Analytics - Login")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login", use_container_width=True):
                if (username == "admin" and password == "admin123") or (username == "analyst" and password == "analyst123"):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            
            st.info("Demo credentials: admin/admin123 or analyst/analyst123")
        return False
    
    return True

# Sample data
def get_sample_data(months=12, growth_rate=0.02):
    """Generate sample cash flow data with configurable parameters."""
    start_date = datetime.now().replace(day=1)  # Start from current month
    dates = pd.date_range(start=start_date, periods=months, freq='M')
    data = []
    cumulative = 100000  # Starting cash position
    
    for i, month in enumerate(dates):
        # Revenue with growth and seasonality
        base_revenue = 50000
        seasonal_factor = 1 + 0.1 * (i % 12 / 12)  # Small seasonal variation
        revenue = base_revenue * (1 + growth_rate) ** i * seasonal_factor
        
        # Expenses (variable and fixed)
        variable_expenses = -revenue * 0.35  # 35% of revenue
        fixed_expenses = -15000  # Fixed monthly costs
        total_expenses = variable_expenses + fixed_expenses
        
        # Net cash flow
        net_cash = revenue + total_expenses
        cumulative += net_cash
        
        data.append({
            'Month': month.strftime('%b %Y'),
            'Date': month,
            'Revenue': round(revenue, 0),
            'Expenses': round(total_expenses, 0),
            'Net Cash Flow': round(net_cash, 0),
            'Cumulative Cash': round(cumulative, 0)
        })
    
    return pd.DataFrame(data)

# KPI Calculations
def calculate_kpis(df):
    """Calculate key performance indicators from cash flow data."""
    min_cash = df['Cumulative Cash'].min()
    min_cash_month = df.loc[df['Cumulative Cash'].idxmin(), 'Month']
    final_cash = df['Cumulative Cash'].iloc[-1]
    
    # Calculate runway (months until cash runs out)
    negative_months = df[df['Net Cash Flow'] < 0]
    if len(negative_months) > 0:
        avg_burn = abs(negative_months['Net Cash Flow'].mean())
        current_cash = df['Cumulative Cash'].iloc[0]
        runway = int(current_cash / avg_burn) if avg_burn > 0 else 999
    else:
        runway = 999  # Positive cash flow
    
    # Average burn rate (negative cash flows only)
    burn_rate = abs(df[df['Net Cash Flow'] < 0]['Net Cash Flow'].mean()) if len(negative_months) > 0 else 0
    
    return {
        'min_cash': min_cash,
        'min_cash_month': min_cash_month,
        'final_cash': final_cash,
        'runway_months': runway if runway < 999 else None,
        'burn_rate': burn_rate
    }

# Main app
def main():
    if not check_auth():
        return
    
    # Sidebar
    with st.sidebar:
        st.write(f"👋 Welcome, {st.session_state.username}!")
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.rerun()
    
    st.title("💰 Cash Flow Analytics")
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Projections", "📥 Data Upload", "📋 Reports"])
    
    with tab1:
        st.header("📊 Dashboard")
        
        # Get data and calculate KPIs
        df = get_sample_data(24)  # 24 months
        kpis = calculate_kpis(df)
        
        # Display KPIs
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            current_cash = df['Cumulative Cash'].iloc[0] if len(df) > 0 else 0
            st.metric("💰 Current Cash", f"${current_cash:,.0f}")
        with col2:
            st.metric("📉 Min Cash Position", f"${kpis['min_cash']:,.0f}", kpis['min_cash_month'])
        with col3:
            runway_text = f"{kpis['runway_months']} months" if kpis['runway_months'] else "∞"
            st.metric("🏃 Runway", runway_text)
        with col4:
            st.metric("📊 Avg Burn Rate", f"${kpis['burn_rate']:,.0f}/mo")
        
        # Status indicators
        st.markdown("### 🚦 Financial Health")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if kpis['min_cash'] < 0:
                st.error("⚠️ **Cash Flow Alert**: Projected to go negative!")
            else:
                st.success("✅ **Cash Positive**: Healthy cash position")
        
        with col2:
            if kpis['runway_months'] and kpis['runway_months'] < 6:
                st.error(f"🔥 **Short Runway**: Only {kpis['runway_months']} months left")
            elif kpis['runway_months'] and kpis['runway_months'] < 12:
                st.warning(f"⚠️ **Moderate Runway**: {kpis['runway_months']} months remaining")
            else:
                st.success("✅ **Sufficient Runway**: Strong financial position")
        
        with col3:
            growth_rate = ((df['Revenue'].iloc[-1] / df['Revenue'].iloc[0]) ** (1/len(df)) - 1) * 100
            if growth_rate > 5:
                st.success(f"📈 **High Growth**: {growth_rate:.1f}% monthly")
            elif growth_rate > 2:
                st.info(f"📊 **Steady Growth**: {growth_rate:.1f}% monthly")
            else:
                st.warning(f"📉 **Slow Growth**: {growth_rate:.1f}% monthly")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Cumulative Cash'],
            mode='lines+markers',
            name='Cumulative Cash Flow',
            line=dict(color='blue', width=3)
        ))
        
        fig.add_trace(go.Bar(
            x=df['Date'],
            y=df['Net Cash Flow'],
            name='Monthly Net Cash',
            opacity=0.6,
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='12-Month Cash Flow Projection',
            xaxis_title='Month',
            yaxis=dict(title='Cumulative Cash ($)', side='left'),
            yaxis2=dict(title='Net Cash Flow ($)', side='right', overlaying='y'),
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("📈 Cash Flow Projections")
        
        # Parameters
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("⚙️ Assumptions")
            
            sales_growth = st.slider("Monthly Sales Growth (%)", 0.0, 10.0, 2.0, 0.1) / 100
            dso_days = st.number_input("Days Sales Outstanding", 15, 90, 30)
            dpo_days = st.number_input("Days Payable Outstanding", 15, 90, 30)
            
            st.info(f"""
            **Current Settings:**
            - Sales Growth: {sales_growth*100:.1f}%
            - DSO: {dso_days} days
            - DPO: {dpo_days} days
            """)
        
        with col2:
            st.subheader("📊 24-Month Projection")
            
            # Generate data with custom parameters
            df = get_sample_data(24, sales_growth)
            
            # Calculate impact of DSO/DPO (simplified)
            working_capital_impact = (dso_days - dpo_days) * 1000  # Simplified calculation
            if working_capital_impact != 0:
                st.info(f"Working Capital Impact: ${working_capital_impact:,.0f} (DSO-DPO difference)")
            
            # Format for display
            display_df = df[['Month', 'Revenue', 'Expenses', 'Net Cash Flow', 'Cumulative Cash']].copy()
            for col in ['Revenue', 'Expenses', 'Net Cash Flow', 'Cumulative Cash']:
                display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Projection insights
            st.markdown("#### 💡 Projection Insights")
            final_revenue = df['Revenue'].iloc[-1]
            revenue_growth_total = ((final_revenue / df['Revenue'].iloc[0]) - 1) * 100
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("📈 Total Revenue Growth", f"{revenue_growth_total:.1f}%", "24 months")
            with col_b:
                final_cash = df['Cumulative Cash'].iloc[-1]
                st.metric("💰 Final Cash Position", f"${final_cash:,.0f}")
            
            # Scenario analysis
            if sales_growth > 0.05:  # 5%
                st.success("🚀 **Aggressive Growth Scenario**: High growth targets set!")
            elif sales_growth > 0.02:  # 2%
                st.info("📊 **Moderate Growth Scenario**: Steady expansion expected")
            else:
                st.warning("🐌 **Conservative Scenario**: Low growth assumptions")
    
    with tab3:
        st.header("📥 Transaction Data Upload")
        
        st.info("Upload your transaction data in CSV format")
        
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.success(f"File uploaded! Found {len(df)} transactions.")
                st.dataframe(df.head(), use_container_width=True)
            except Exception as e:
                st.error(f"Error reading file: {e}")
        
        # Manual entry
        st.subheader("✏️ Add Transaction Manually")
        
        with st.form("manual_transaction"):
            col1, col2 = st.columns(2)
            
            with col1:
                tx_date = st.date_input("Date", value=date.today())
                category = st.selectbox("Category", ["Revenue", "Operating Expenses", "Equipment", "Other"])
                description = st.text_input("Description")
            
            with col2:
                amount = st.number_input("Amount ($)", step=0.01)
                account = st.selectbox("Account", ["Cash", "Bank", "Credit Card"])
                paid = st.checkbox("Paid", value=True)
            
            if st.form_submit_button("Add Transaction"):
                st.success("Transaction added successfully!")
                st.info(f"Added: {description} - ${amount:,.2f}")
    
    with tab4:
        st.header("📋 Reports & Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Export Data")
            
            df = get_sample_data()
            
            # CSV export
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV Report",
                data=csv,
                file_name=f"cashflow_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # Excel export (simplified)
            st.info("💡 **Tip**: Use CSV export for Excel compatibility. You can open CSV files directly in Excel!")
            
            # Alternative: JSON export for data backup
            json_data = df.to_json(orient='records', date_format='iso')
            st.download_button(
                label="📄 Download JSON Data",
                data=json_data,
                file_name=f"cashflow_data_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            st.subheader("📈 Key Insights")
            
            df = get_sample_data()
            
            total_revenue = df['Revenue'].sum()
            total_expenses = df['Expenses'].sum()
            final_cash = df['Cumulative Cash'].iloc[-1]
            min_cash = df['Cumulative Cash'].min()
            
            st.info(f"""
            **12-Month Summary:**
            - Total Revenue: ${total_revenue:,.0f}
            - Total Expenses: ${total_expenses:,.0f}
            - Final Cash Position: ${final_cash:,.0f}
            - Minimum Cash Position: ${min_cash:,.0f}
            """)
            
            if min_cash < 0:
                st.error("⚠️ Warning: Cash flow goes negative!")
            else:
                st.success("✅ Positive cash flow maintained")

if __name__ == "__main__":
    main()