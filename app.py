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
def get_sample_data():
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
    data = []
    
    for i, month in enumerate(dates):
        revenue = 50000 + (i * 2000)  # Growing revenue
        expenses = -30000 - (i * 500)  # Growing expenses
        net_cash = revenue + expenses
        
        data.append({
            'Month': month.strftime('%b %Y'),
            'Date': month,
            'Revenue': revenue,
            'Expenses': expenses,
            'Net Cash Flow': net_cash,
            'Cumulative Cash': sum([d['Net Cash Flow'] for d in data]) + net_cash
        })
    
    return pd.DataFrame(data)

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
        
        # Sample KPIs
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Current Cash", "$125,000", "+$15,000")
        with col2:
            st.metric("📉 Min Cash Position", "$45,000", "Mar 2024")
        with col3:
            st.metric("🏃 Runway", "18 months", "+2 months")
        with col4:
            st.metric("📊 Burn Rate", "$8,500/mo", "-$500")
        
        # Sample chart
        df = get_sample_data()
        
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
            
            df = get_sample_data()
            
            # Apply growth rate
            for i in range(len(df)):
                df.loc[i, 'Revenue'] = df.loc[i, 'Revenue'] * (1 + sales_growth) ** i
                df.loc[i, 'Net Cash Flow'] = df.loc[i, 'Revenue'] + df.loc[i, 'Expenses']
            
            # Recalculate cumulative
            df['Cumulative Cash'] = df['Net Cash Flow'].cumsum()
            
            # Format for display
            display_df = df[['Month', 'Revenue', 'Expenses', 'Net Cash Flow', 'Cumulative Cash']].copy()
            for col in ['Revenue', 'Expenses', 'Net Cash Flow', 'Cumulative Cash']:
                display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
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
            
            # Excel export
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Cash Flow', index=False)
                
                # Add formatting
                workbook = writer.book
                worksheet = writer.sheets['Cash Flow']
                
                money_format = workbook.add_format({'num_format': '$#,##0'})
                worksheet.set_column('C:F', 12, money_format)
            
            st.download_button(
                label="📊 Download Excel Report",
                data=output.getvalue(),
                file_name=f"cashflow_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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