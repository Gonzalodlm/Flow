import streamlit as st
from sqlmodel import Session, select
from src.auth.simple_auth import require_auth, get_current_company_id
from src.core.db import get_session
from src.core.models import Assumption, Scenario, Company, DEFAULT_ASSUMPTIONS
from src.ui.components import display_success_message, display_error_message

st.set_page_config(page_title="Assumptions", page_icon="⚙️", layout="wide")

def main():
    if not require_auth():
        return
    
    st.title("⚙️ Supuestos y Drivers")
    st.markdown("---")
    
    company_id = get_current_company_id()
    if not company_id:
        st.error("No company selected.")
        return
    
    with next(get_session()) as session:
        company = session.get(Company, company_id)
        if not company:
            st.error("Company not found.")
            return
        
        st.markdown(f"### 🏢 {company.name} - Business Assumptions")
        
        # Get base scenario
        base_scenario = session.exec(
            select(Scenario).where(
                Scenario.company_id == company_id,
                Scenario.base == True
            )
        ).first()
        
        if not base_scenario:
            # Create base scenario if it doesn't exist
            base_scenario = Scenario(
                name="Base Case",
                base=True,
                company_id=company_id,
                params={}
            )
            session.add(base_scenario)
            session.commit()
            session.refresh(base_scenario)
        
        # Get current assumptions
        current_assumptions = get_assumptions_dict(session, company_id, base_scenario.id)
        
        # Display assumption form
        updated_assumptions = display_assumptions_form(current_assumptions, company.base_currency)
        
        if updated_assumptions and updated_assumptions != current_assumptions:
            save_assumptions(session, company_id, base_scenario.id, updated_assumptions)

def get_assumptions_dict(session: Session, company_id: int, scenario_id: int) -> dict:
    """Get assumptions as a dictionary."""
    assumptions = {}
    
    # Start with defaults
    assumptions.update(DEFAULT_ASSUMPTIONS)
    
    # Override with database values
    db_assumptions = session.exec(
        select(Assumption).where(
            Assumption.company_id == company_id,
            Assumption.scenario_id == scenario_id
        )
    ).all()
    
    for assumption in db_assumptions:
        assumptions[assumption.key] = assumption.value
    
    return assumptions

def save_assumptions(session: Session, company_id: int, scenario_id: int, assumptions: dict):
    """Save assumptions to database."""
    try:
        for key, value in assumptions.items():
            # Check if assumption exists
            existing = session.exec(
                select(Assumption).where(
                    Assumption.company_id == company_id,
                    Assumption.scenario_id == scenario_id,
                    Assumption.key == key
                )
            ).first()
            
            if existing:
                existing.value = value
            else:
                new_assumption = Assumption(
                    company_id=company_id,
                    scenario_id=scenario_id,
                    key=key,
                    value=value
                )
                session.add(new_assumption)
        
        session.commit()
        display_success_message("Assumptions saved successfully!")
        st.rerun()
        
    except Exception as e:
        session.rollback()
        display_error_message("Failed to save assumptions", str(e))

def display_assumptions_form(assumptions: dict, currency: str) -> dict:
    """Display comprehensive assumptions form."""
    st.markdown("### 📊 Business Drivers & Assumptions")
    
    updated_assumptions = {}
    
    with st.form("assumptions_form"):
        # Revenue & Growth Section
        st.markdown("#### 📈 Revenue & Growth")
        col1, col2 = st.columns(2)
        
        with col1:
            updated_assumptions['sales_growth'] = st.number_input(
                "Monthly Sales Growth Rate (%)",
                value=assumptions.get('sales_growth', 0.05) * 100,
                min_value=-50.0,
                max_value=100.0,
                step=0.1,
                format="%.2f",
                help="Expected monthly growth rate for sales revenue"
            ) / 100
            
            updated_assumptions['dso_days'] = st.number_input(
                "Days Sales Outstanding (DSO)",
                value=assumptions.get('dso_days', 30),
                min_value=0,
                max_value=365,
                step=1,
                help="Average number of days to collect receivables from customers"
            )
        
        with col2:
            updated_assumptions['revenue_seasonality'] = st.number_input(
                "Revenue Seasonality Factor (%)",
                value=assumptions.get('revenue_seasonality', 0.0) * 100,
                min_value=-50.0,
                max_value=100.0,
                step=1.0,
                format="%.1f",
                help="Seasonal adjustment to revenue (e.g., holiday boost)"
            ) / 100
            
            updated_assumptions['customer_concentration'] = st.number_input(
                "Top Customer Concentration (%)",
                value=assumptions.get('customer_concentration', 0.3) * 100,
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                format="%.1f",
                help="Percentage of revenue from top customer"
            ) / 100
        
        st.markdown("---")
        
        # Operating Expenses Section
        st.markdown("#### 💼 Operating Expenses")
        col1, col2 = st.columns(2)
        
        with col1:
            updated_assumptions['opex_growth'] = st.number_input(
                "Monthly OpEx Growth Rate (%)",
                value=assumptions.get('opex_growth', 0.02) * 100,
                min_value=-10.0,
                max_value=50.0,
                step=0.1,
                format="%.2f",
                help="Expected monthly growth rate for operating expenses"
            ) / 100
            
            updated_assumptions['dpo_days'] = st.number_input(
                "Days Payable Outstanding (DPO)",
                value=assumptions.get('dpo_days', 30),
                min_value=0,
                max_value=120,
                step=1,
                help="Average number of days to pay suppliers"
            )
            
            updated_assumptions['salary_inflation'] = st.number_input(
                "Annual Salary Inflation (%)",
                value=assumptions.get('salary_inflation', 0.05) * 100,
                min_value=0.0,
                max_value=20.0,
                step=0.1,
                format="%.1f",
                help="Expected annual increase in salary costs"
            ) / 100
        
        with col2:
            updated_assumptions['variable_cost_ratio'] = st.number_input(
                "Variable Cost Ratio (%)",
                value=assumptions.get('variable_cost_ratio', 0.3) * 100,
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                format="%.1f",
                help="Variable costs as percentage of revenue"
            ) / 100
            
            updated_assumptions['fixed_costs_monthly'] = st.number_input(
                f"Fixed Costs Monthly ({currency})",
                value=assumptions.get('fixed_costs_monthly', 5000.0),
                min_value=0.0,
                step=100.0,
                format="%.0f",
                help="Monthly fixed operating costs (rent, utilities, etc.)"
            )
            
            updated_assumptions['inventory_days'] = st.number_input(
                "Inventory Days",
                value=assumptions.get('inventory_days', 15),
                min_value=0,
                max_value=365,
                step=1,
                help="Days of inventory on hand"
            )
        
        st.markdown("---")
        
        # Capital & Investment Section
        st.markdown("#### 🏗️ Capital & Investment")
        col1, col2 = st.columns(2)
        
        with col1:
            updated_assumptions['capex_monthly'] = st.number_input(
                f"Monthly CapEx ({currency})",
                value=assumptions.get('capex_monthly', 0.0),
                min_value=0.0,
                step=100.0,
                format="%.0f",
                help="Expected monthly capital expenditure"
            )
            
            updated_assumptions['depreciation_rate'] = st.number_input(
                "Annual Depreciation Rate (%)",
                value=assumptions.get('depreciation_rate', 0.15) * 100,
                min_value=0.0,
                max_value=50.0,
                step=1.0,
                format="%.1f",
                help="Annual depreciation rate for assets"
            ) / 100
        
        with col2:
            updated_assumptions['capex_intensity'] = st.number_input(
                "CapEx Intensity (% of Revenue)",
                value=assumptions.get('capex_intensity', 0.05) * 100,
                min_value=0.0,
                max_value=50.0,
                step=0.5,
                format="%.1f",
                help="Capital expenditure as percentage of revenue"
            ) / 100
            
            updated_assumptions['working_capital_ratio'] = st.number_input(
                "Working Capital Ratio (% of Revenue)",
                value=assumptions.get('working_capital_ratio', 0.1) * 100,
                min_value=-50.0,
                max_value=50.0,
                step=1.0,
                format="%.1f",
                help="Working capital change as percentage of revenue"
            ) / 100
        
        st.markdown("---")
        
        # Tax & Legal Section
        st.markdown("#### 🏛️ Tax & Legal")
        col1, col2 = st.columns(2)
        
        with col1:
            updated_assumptions['tax_rate'] = st.number_input(
                "Corporate Tax Rate (%)",
                value=assumptions.get('tax_rate', 0.22) * 100,
                min_value=0.0,
                max_value=50.0,
                step=0.5,
                format="%.1f",
                help="Corporate income tax rate"
            ) / 100
            
            updated_assumptions['tax_payment_delay'] = st.number_input(
                "Tax Payment Delay (Months)",
                value=assumptions.get('tax_payment_delay', 3),
                min_value=0,
                max_value=12,
                step=1,
                help="Months delay between earning and paying taxes"
            )
        
        with col2:
            updated_assumptions['legal_fees_annual'] = st.number_input(
                f"Annual Legal Fees ({currency})",
                value=assumptions.get('legal_fees_annual', 5000.0),
                min_value=0.0,
                step=500.0,
                format="%.0f",
                help="Expected annual legal and compliance costs"
            )
            
            updated_assumptions['regulatory_risk'] = st.selectbox(
                "Regulatory Risk Level",
                options=[0.0, 0.05, 0.1, 0.15, 0.2],
                index=0,
                format_func=lambda x: f"{x*100:.0f}% - {'Low' if x < 0.1 else 'Medium' if x < 0.15 else 'High'}",
                help="Regulatory risk factor affecting costs"
            )
        
        st.markdown("---")
        
        # Debt & Financing Section
        st.markdown("#### 💳 Debt & Financing")
        col1, col2 = st.columns(2)
        
        with col1:
            updated_assumptions['debt_principal'] = st.number_input(
                f"Outstanding Debt Principal ({currency})",
                value=assumptions.get('debt_principal', 0.0),
                min_value=0.0,
                step=1000.0,
                format="%.0f",
                help="Current outstanding debt principal amount"
            )
            
            updated_assumptions['interest_rate'] = st.number_input(
                "Annual Interest Rate (%)",
                value=assumptions.get('interest_rate', 0.12) * 100,
                min_value=0.0,
                max_value=30.0,
                step=0.1,
                format="%.2f",
                help="Annual interest rate on debt"
            ) / 100
            
            updated_assumptions['debt_term_months'] = st.number_input(
                "Debt Term (Months)",
                value=assumptions.get('debt_term_months', 60),
                min_value=1,
                max_value=360,
                step=1,
                help="Remaining term of debt in months"
            )
        
        with col2:
            updated_assumptions['credit_line_available'] = st.number_input(
                f"Available Credit Line ({currency})",
                value=assumptions.get('credit_line_available', 0.0),
                min_value=0.0,
                step=1000.0,
                format="%.0f",
                help="Available credit line for emergencies"
            )
            
            updated_assumptions['debt_covenant_ratio'] = st.number_input(
                "Debt Covenant Ratio (Min DSCR)",
                value=assumptions.get('debt_covenant_ratio', 1.25),
                min_value=0.0,
                max_value=5.0,
                step=0.05,
                format="%.2f",
                help="Minimum debt service coverage ratio required"
            )
            
            updated_assumptions['refinancing_risk'] = st.selectbox(
                "Refinancing Risk",
                options=[0.0, 0.05, 0.1, 0.2, 0.3],
                index=0,
                format_func=lambda x: f"{x*100:.0f}% - {'Low' if x < 0.1 else 'Medium' if x < 0.2 else 'High'}",
                help="Risk of refinancing difficulties"
            )
        
        st.markdown("---")
        
        # Cash Management Section
        st.markdown("#### 💰 Cash Management")
        col1, col2 = st.columns(2)
        
        with col1:
            updated_assumptions['min_cash_target'] = st.number_input(
                f"Minimum Cash Target ({currency})",
                value=assumptions.get('min_cash_target', 10000.0),
                min_value=0.0,
                step=1000.0,
                format="%.0f",
                help="Minimum cash level to maintain for operations"
            )
            
            updated_assumptions['cash_conversion_cycle'] = st.number_input(
                "Cash Conversion Cycle (Days)",
                value=assumptions.get('cash_conversion_cycle', 45),
                min_value=-180,
                max_value=365,
                step=1,
                help="DSO + Inventory Days - DPO"
            )
        
        with col2:
            updated_assumptions['cash_yield'] = st.number_input(
                "Cash Investment Yield (%)",
                value=assumptions.get('cash_yield', 0.02) * 100,
                min_value=0.0,
                max_value=10.0,
                step=0.1,
                format="%.2f",
                help="Annual yield on cash investments"
            ) / 100
            
            updated_assumptions['emergency_fund_ratio'] = st.number_input(
                "Emergency Fund Ratio (Months of OpEx)",
                value=assumptions.get('emergency_fund_ratio', 3.0),
                min_value=0.0,
                max_value=12.0,
                step=0.5,
                format="%.1f",
                help="Months of operating expenses to keep as emergency fund"
            )
        
        # Submit button
        st.markdown("---")
        submitted = st.form_submit_button("💾 Save Assumptions", type="primary", use_container_width=True)
        
        if submitted:
            return updated_assumptions
    
    return assumptions

if __name__ == "__main__":
    main()