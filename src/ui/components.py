import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import date, datetime
import plotly.graph_objects as go
import plotly.express as px
from src.core.schemas import CashFlowProjection, KPIMetrics
from src.core.utils import format_currency

def display_kpi_cards(kpis: KPIMetrics, currency: str = "USD"):
    """Display KPI metrics in card format."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Current Cash",
            value=format_currency(kpis.final_cash, currency),
            delta=None
        )
    
    with col2:
        st.metric(
            label="📉 Min Cash Position",
            value=format_currency(kpis.min_cash, currency),
            delta=kpis.min_cash_month.strftime('%b %Y')
        )
    
    with col3:
        runway_text = f"{kpis.months_of_runway} months" if kpis.months_of_runway else "∞"
        st.metric(
            label="🏃 Runway",
            value=runway_text,
            delta=None
        )
    
    with col4:
        dscr_text = f"{kpis.dscr:.2f}" if kpis.dscr else "N/A"
        st.metric(
            label="📊 DSCR",
            value=dscr_text,
            delta=None
        )

def create_cash_flow_chart(projections: List[CashFlowProjection], currency: str = "USD") -> go.Figure:
    """Create cash flow visualization chart."""
    if not projections:
        return go.Figure()
    
    months = [p.month for p in projections]
    cumulative_cash = [p.cumulative_cash for p in projections]
    net_cash = [p.net_cash for p in projections]
    
    fig = go.Figure()
    
    # Cumulative cash line
    fig.add_trace(go.Scatter(
        x=months,
        y=cumulative_cash,
        mode='lines+markers',
        name='Cumulative Cash',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=6),
        hovertemplate=f'%{{x}}<br>Cumulative: {currency} %{{y:,.0f}}<extra></extra>'
    ))
    
    # Net cash flow bars
    colors = ['#2ca02c' if x > 0 else '#d62728' for x in net_cash]
    fig.add_trace(go.Bar(
        x=months,
        y=net_cash,
        name='Net Cash Flow',
        marker_color=colors,
        opacity=0.7,
        yaxis='y2',
        hovertemplate=f'%{{x}}<br>Net Flow: {currency} %{{y:,.0f}}<extra></extra>'
    ))
    
    # Add zero line for cumulative cash
    fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
    
    fig.update_layout(
        title='Cash Flow Projection - 24 Months',
        xaxis_title='Month',
        yaxis=dict(
            title=f'Cumulative Cash ({currency})',
            side='left',
            tickformat=',.0f'
        ),
        yaxis2=dict(
            title=f'Net Cash Flow ({currency})',
            side='right',
            overlaying='y',
            tickformat=',.0f'
        ),
        hovermode='x unified',
        legend=dict(x=0.01, y=0.99),
        template='plotly_white',
        height=500
    )
    
    return fig

def display_projections_table(
    projections: List[CashFlowProjection], 
    currency: str = "USD",
    page_size: int = 12
):
    """Display cash flow projections in a paginated table."""
    if not projections:
        st.warning("No projections available.")
        return
    
    # Convert to DataFrame for better display
    df_data = []
    for p in projections:
        df_data.append({
            'Month': p.month.strftime('%b %Y'),
            'Cash In': p.cash_in,
            'Cash Out': p.cash_out,
            'Net Cash': p.net_cash,
            'Cumulative': p.cumulative_cash
        })
    
    df = pd.DataFrame(df_data)
    
    # Add pagination
    total_pages = len(df) // page_size + (1 if len(df) % page_size > 0 else 0)
    
    if total_pages > 1:
        page = st.selectbox(
            "Select Page", 
            range(1, total_pages + 1),
            format_func=lambda x: f"Page {x} ({(x-1)*page_size + 1}-{min(x*page_size, len(df))})"
        )
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, len(df))
        df_display = df.iloc[start_idx:end_idx]
    else:
        df_display = df
    
    # Format currency columns
    currency_cols = ['Cash In', 'Cash Out', 'Net Cash', 'Cumulative']
    
    def format_currency_value(val):
        if pd.isna(val):
            return val
        return f"{currency} {val:,.0f}"
    
    df_formatted = df_display.copy()
    for col in currency_cols:
        df_formatted[col] = df_formatted[col].apply(format_currency_value)
    
    st.dataframe(
        df_formatted,
        use_container_width=True,
        hide_index=True
    )

def create_scenario_comparison_chart(
    scenarios: List[Dict], 
    currency: str = "USD"
) -> go.Figure:
    """Create scenario comparison chart."""
    if not scenarios:
        return go.Figure()
    
    fig = go.Figure()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, scenario in enumerate(scenarios):
        projections = scenario['projections']
        months = [p.month for p in projections]
        cumulative_cash = [p.cumulative_cash for p in projections]
        
        fig.add_trace(go.Scatter(
            x=months,
            y=cumulative_cash,
            mode='lines+markers',
            name=scenario['scenario_name'],
            line=dict(color=colors[i % len(colors)], width=3),
            marker=dict(size=6),
            hovertemplate=f'%{{x}}<br>{scenario["scenario_name"]}: {currency} %{{y:,.0f}}<extra></extra>'
        ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
    
    fig.update_layout(
        title='Scenario Comparison - Cumulative Cash Flow',
        xaxis_title='Month',
        yaxis_title=f'Cumulative Cash ({currency})',
        hovermode='x unified',
        legend=dict(x=0.01, y=0.99),
        template='plotly_white',
        height=500
    )
    
    return fig

def display_assumptions_form(
    assumptions: Dict[str, float],
    scenario_name: str = "Base Case"
) -> Dict[str, float]:
    """Display and collect assumptions in a form."""
    st.subheader(f"📊 {scenario_name} - Assumptions")
    
    updated_assumptions = {}
    
    with st.form(f"assumptions_form_{scenario_name}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Revenue & Growth**")
            updated_assumptions['sales_growth'] = st.number_input(
                "Monthly Sales Growth (%)",
                value=assumptions.get('sales_growth', 0.05) * 100,
                min_value=-50.0,
                max_value=100.0,
                step=0.1,
                format="%.1f",
                help="Expected monthly growth rate for sales"
            ) / 100
            
            updated_assumptions['dso_days'] = st.number_input(
                "Days Sales Outstanding",
                value=assumptions.get('dso_days', 30),
                min_value=0,
                max_value=120,
                step=1,
                help="Average days to collect receivables"
            )
            
            st.write("**Operating Expenses**")
            updated_assumptions['opex_growth'] = st.number_input(
                "Monthly OpEx Growth (%)",
                value=assumptions.get('opex_growth', 0.02) * 100,
                min_value=-10.0,
                max_value=50.0,
                step=0.1,
                format="%.1f",
                help="Expected monthly growth rate for operating expenses"
            ) / 100
            
            updated_assumptions['dpo_days'] = st.number_input(
                "Days Payable Outstanding",
                value=assumptions.get('dpo_days', 30),
                min_value=0,
                max_value=120,
                step=1,
                help="Average days to pay suppliers"
            )
        
        with col2:
            st.write("**Capital & Financing**")
            updated_assumptions['capex_monthly'] = st.number_input(
                "Monthly CapEx ($)",
                value=assumptions.get('capex_monthly', 0.0),
                min_value=0.0,
                step=100.0,
                format="%.0f",
                help="Expected monthly capital expenditure"
            )
            
            updated_assumptions['tax_rate'] = st.number_input(
                "Tax Rate (%)",
                value=assumptions.get('tax_rate', 0.22) * 100,
                min_value=0.0,
                max_value=50.0,
                step=0.1,
                format="%.1f",
                help="Corporate tax rate"
            ) / 100
            
            st.write("**Debt & Cash Management**")
            updated_assumptions['debt_principal'] = st.number_input(
                "Outstanding Debt ($)",
                value=assumptions.get('debt_principal', 0.0),
                min_value=0.0,
                step=1000.0,
                format="%.0f",
                help="Current outstanding debt principal"
            )
            
            updated_assumptions['interest_rate'] = st.number_input(
                "Annual Interest Rate (%)",
                value=assumptions.get('interest_rate', 0.12) * 100,
                min_value=0.0,
                max_value=30.0,
                step=0.1,
                format="%.1f",
                help="Annual interest rate on debt"
            ) / 100
            
            updated_assumptions['min_cash_target'] = st.number_input(
                "Minimum Cash Target ($)",
                value=assumptions.get('min_cash_target', 10000.0),
                min_value=0.0,
                step=1000.0,
                format="%.0f",
                help="Minimum cash level to maintain"
            )
        
        submitted = st.form_submit_button("Update Assumptions", type="primary")
        
        if submitted:
            st.success("Assumptions updated successfully!")
            return updated_assumptions
    
    return assumptions

def display_transaction_upload():
    """Display transaction upload interface."""
    st.subheader("📁 Upload Transactions")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=['csv', 'xlsx'],
        help="File should contain columns: date, category, description, amount, currency, account, paid"
    )
    
    if uploaded_file is not None:
        try:
            # Read file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"File uploaded successfully! Found {len(df)} transactions.")
            
            # Display preview
            st.write("**Preview (first 5 rows):**")
            st.dataframe(df.head(), use_container_width=True)
            
            # Column mapping
            st.write("**Column Mapping:**")
            expected_columns = ['date', 'category', 'description', 'amount', 'currency', 'account', 'paid']
            
            col_mapping = {}
            cols = st.columns(len(expected_columns))
            
            for i, expected_col in enumerate(expected_columns):
                with cols[i]:
                    col_mapping[expected_col] = st.selectbox(
                        f"Map '{expected_col}'",
                        options=[''] + list(df.columns),
                        index=0,
                        key=f"mapping_{expected_col}"
                    )
            
            # Validate mapping
            missing_mappings = [col for col, mapping in col_mapping.items() if not mapping]
            
            if not missing_mappings:
                if st.button("Import Transactions", type="primary"):
                    # Process and return mapped data
                    mapped_df = df.rename(columns={v: k for k, v in col_mapping.items() if v})
                    st.session_state['uploaded_transactions'] = mapped_df
                    st.success("Transactions ready for import!")
            else:
                st.warning(f"Please map all columns. Missing: {', '.join(missing_mappings)}")
                
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    return uploaded_file is not None

def display_manual_transaction_form():
    """Display manual transaction entry form."""
    st.subheader("✏️ Add Transaction Manually")
    
    with st.form("manual_transaction"):
        col1, col2 = st.columns(2)
        
        with col1:
            tx_date = st.date_input("Date", value=date.today())
            category = st.text_input("Category", placeholder="e.g., Sales, Rent, Salary")
            description = st.text_input("Description", placeholder="Transaction description")
            amount = st.number_input("Amount ($)", step=0.01, format="%.2f")
        
        with col2:
            currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "UYU"], index=0)
            account = st.selectbox("Account", ["Revenue", "Operating Expenses", "Equipment", "Loan"])
            paid = st.checkbox("Paid", value=True)
            recurrence = st.selectbox("Recurrence", ["none", "monthly", "quarterly", "weekly"])
        
        submitted = st.form_submit_button("Add Transaction", type="primary")
        
        if submitted and amount != 0:
            transaction_data = {
                'date': tx_date,
                'category': category,
                'description': description,
                'amount': amount,
                'currency': currency,
                'account': account,
                'paid': paid,
                'recurrence': recurrence
            }
            
            return transaction_data
    
    return None

def display_loading_spinner(message: str = "Processing..."):
    """Display a loading spinner with message."""
    with st.spinner(message):
        return st.empty()

def display_error_message(message: str, details: str = None):
    """Display a standardized error message."""
    st.error(f"❌ {message}")
    if details:
        with st.expander("Error Details"):
            st.code(details)

def display_success_message(message: str):
    """Display a standardized success message."""
    st.success(f"✅ {message}")