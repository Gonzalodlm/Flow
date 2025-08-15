import streamlit as st
from sqlmodel import Session, select
from typing import List, Dict
from src.auth.auth import require_auth, get_current_company_id
from src.core.db import get_session
from src.core.logic import CashFlowEngine
from src.core.models import Scenario, Assumption, Company, DEFAULT_ASSUMPTIONS
from src.ui.components import (
    create_scenario_comparison_chart, display_kpi_cards,
    display_success_message, display_error_message
)

st.set_page_config(page_title="Scenarios", page_icon="🧪", layout="wide")

def main():
    if not require_auth():
        return
    
    st.title("🧪 Escenarios")
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
        
        st.markdown(f"### 🏢 {company.name} - Scenario Analysis")
        
        # Tabs for different scenario operations
        tab1, tab2, tab3 = st.tabs(["📊 Compare Scenarios", "🆕 Create Scenario", "⚙️ Manage Scenarios"])
        
        with tab1:
            handle_compare_scenarios(session, company_id, company)
        
        with tab2:
            handle_create_scenario(session, company_id)
        
        with tab3:
            handle_manage_scenarios(session, company_id)

def handle_compare_scenarios(session: Session, company_id: int, company):
    """Handle scenario comparison."""
    st.markdown("### 📊 Scenario Comparison")
    
    # Get available scenarios
    scenarios = session.exec(
        select(Scenario).where(Scenario.company_id == company_id)
    ).all()
    
    if len(scenarios) < 2:
        st.warning("You need at least 2 scenarios to perform comparison. Create additional scenarios first.")
        return
    
    # Scenario selection
    scenario_options = {s.name: s.id for s in scenarios}
    
    selected_scenarios = st.multiselect(
        "Select scenarios to compare",
        options=list(scenario_options.keys()),
        default=list(scenario_options.keys())[:3],  # Default to first 3
        help="Select 2-4 scenarios for comparison"
    )
    
    if len(selected_scenarios) < 2:
        st.warning("Please select at least 2 scenarios for comparison.")
        return
    
    if len(selected_scenarios) > 4:
        st.warning("Please select no more than 4 scenarios for better visualization.")
        return
    
    # Run comparison
    with st.spinner("Running scenario analysis..."):
        engine = CashFlowEngine(session, company_id)
        
        scenario_results = []
        for scenario_name in selected_scenarios:
            scenario_id = scenario_options[scenario_name]
            projections = engine.project_cash_flow(scenario_id, months=24)
            kpis = engine.calculate_kpis(projections)
            
            scenario_results.append({
                'scenario_name': scenario_name,
                'projections': projections,
                'kpis': kpis,
                'scenario_id': scenario_id
            })
    
    # Display comparison chart
    st.markdown("#### 📈 Cash Flow Comparison")
    comparison_chart = create_scenario_comparison_chart(scenario_results, company.base_currency)
    st.plotly_chart(comparison_chart, use_container_width=True)
    
    # KPI comparison table
    st.markdown("#### 📊 KPI Comparison")
    
    kpi_data = []
    for result in scenario_results:
        kpis = result['kpis']
        kpi_data.append({
            'Scenario': result['scenario_name'],
            'Min Cash': f"{company.base_currency} {kpis.min_cash:,.0f}",
            'Min Cash Month': kpis.min_cash_month.strftime('%b %Y'),
            'Final Cash': f"{company.base_currency} {kpis.final_cash:,.0f}",
            'Runway (Months)': kpis.months_of_runway or 'N/A',
            'Avg Burn Rate': f"{company.base_currency} {kpis.avg_burn_rate:,.0f}",
            'DSCR': f"{kpis.dscr:.2f}" if kpis.dscr else 'N/A'
        })
    
    import pandas as pd
    kpi_df = pd.DataFrame(kpi_data)
    st.dataframe(kpi_df, use_container_width=True, hide_index=True)
    
    # Risk analysis
    st.markdown("#### ⚠️ Risk Analysis")
    
    # Find scenarios with cash flow issues
    risk_scenarios = []
    for result in scenario_results:
        kpis = result['kpis']
        risk_factors = []
        
        if kpis.min_cash < 0:
            risk_factors.append("Negative cash position")
        
        if kpis.months_of_runway and kpis.months_of_runway < 6:
            risk_factors.append("Short runway (<6 months)")
        
        if kpis.dscr and kpis.dscr < 1.0:
            risk_factors.append("DSCR below 1.0")
        
        if risk_factors:
            risk_scenarios.append({
                'scenario': result['scenario_name'],
                'risks': risk_factors
            })
    
    if risk_scenarios:
        st.error("⚠️ **Risk Alert**: The following scenarios show concerning metrics:")
        for risk in risk_scenarios:
            st.write(f"- **{risk['scenario']}**: {', '.join(risk['risks'])}")
    else:
        st.success("✅ All selected scenarios show healthy cash flow metrics.")
    
    # Summary insights
    st.markdown("#### 💡 Key Insights")
    
    best_scenario = max(scenario_results, key=lambda x: x['kpis'].final_cash)
    worst_scenario = min(scenario_results, key=lambda x: x['kpis'].final_cash)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success(f"""
        **Best Case: {best_scenario['scenario_name']}**
        - Final cash: {company.base_currency} {best_scenario['kpis'].final_cash:,.0f}
        - Min cash: {company.base_currency} {best_scenario['kpis'].min_cash:,.0f}
        """)
    
    with col2:
        st.error(f"""
        **Worst Case: {worst_scenario['scenario_name']}**
        - Final cash: {company.base_currency} {worst_scenario['kpis'].final_cash:,.0f}
        - Min cash: {company.base_currency} {worst_scenario['kpis'].min_cash:,.0f}
        """)

def handle_create_scenario(session: Session, company_id: int):
    """Handle scenario creation."""
    st.markdown("### 🆕 Create New Scenario")
    
    # Get base scenario for reference
    base_scenario = session.exec(
        select(Scenario).where(
            Scenario.company_id == company_id,
            Scenario.base == True
        )
    ).first()
    
    if not base_scenario:
        st.error("No base scenario found. Please create a base scenario first.")
        return
    
    # Get base assumptions
    base_assumptions = get_scenario_assumptions(session, company_id, base_scenario.id)
    
    with st.form("create_scenario"):
        scenario_name = st.text_input(
            "Scenario Name",
            placeholder="e.g., Optimistic Growth, Economic Downturn, Best Case",
            help="Give your scenario a descriptive name"
        )
        
        scenario_description = st.text_area(
            "Description (Optional)",
            placeholder="Describe the key assumptions of this scenario...",
            help="Optional description of scenario assumptions"
        )
        
        st.markdown("#### 📊 Adjust Key Assumptions")
        st.write("Modify assumptions relative to base case:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Revenue & Growth**")
            
            sales_growth_adj = st.number_input(
                "Sales Growth Adjustment (%)",
                value=0.0,
                min_value=-100.0,
                max_value=500.0,
                step=0.5,
                format="%.1f",
                help="Adjust monthly sales growth rate"
            )
            
            dso_adj = st.number_input(
                "DSO Adjustment (days)",
                value=0,
                min_value=-90,
                max_value=90,
                step=1,
                help="Adjust Days Sales Outstanding"
            )
            
            st.markdown("**Costs & Expenses**")
            
            opex_growth_adj = st.number_input(
                "OpEx Growth Adjustment (%)",
                value=0.0,
                min_value=-50.0,
                max_value=100.0,
                step=0.1,
                format="%.1f",
                help="Adjust operating expense growth rate"
            )
            
            variable_cost_adj = st.number_input(
                "Variable Cost Ratio Adjustment (%)",
                value=0.0,
                min_value=-50.0,
                max_value=50.0,
                step=0.5,
                format="%.1f",
                help="Adjust variable cost percentage"
            )
        
        with col2:
            st.markdown("**Capital & Investment**")
            
            capex_adj = st.number_input(
                "Monthly CapEx Adjustment ($)",
                value=0.0,
                step=100.0,
                format="%.0f",
                help="Adjust monthly capital expenditure"
            )
            
            st.markdown("**Market Conditions**")
            
            market_risk = st.selectbox(
                "Market Risk Factor",
                options=[0.0, 0.05, 0.1, 0.15, 0.2, 0.3],
                index=0,
                format_func=lambda x: f"{x*100:.0f}% - {'No Risk' if x == 0 else 'Low' if x < 0.1 else 'Medium' if x < 0.2 else 'High'}",
                help="Overall market risk affecting the business"
            )
            
            customer_loss_risk = st.number_input(
                "Customer Loss Risk (%)",
                value=0.0,
                min_value=0.0,
                max_value=50.0,
                step=1.0,
                format="%.0f",
                help="Risk of losing major customers"
            )
            
            inflation_factor = st.number_input(
                "Inflation Factor (%)",
                value=0.0,
                min_value=-10.0,
                max_value=30.0,
                step=0.5,
                format="%.1f",
                help="Additional inflation affecting costs"
            )
        
        st.markdown("#### 🎯 Scenario Type")
        
        scenario_type = st.selectbox(
            "Scenario Category",
            options=["Custom", "Optimistic", "Pessimistic", "Conservative", "Aggressive Growth", "Crisis Management"],
            help="Categorize your scenario for easier organization"
        )
        
        if scenario_type != "Custom":
            st.info(f"💡 **{scenario_type} Scenario**: Consider typical adjustments for this scenario type")
        
        submitted = st.form_submit_button("🆕 Create Scenario", type="primary")
        
        if submitted:
            if not scenario_name:
                st.error("Please provide a scenario name.")
                return
            
            # Check if scenario name already exists
            existing = session.exec(
                select(Scenario).where(
                    Scenario.company_id == company_id,
                    Scenario.name == scenario_name
                )
            ).first()
            
            if existing:
                st.error("A scenario with this name already exists.")
                return
            
            try:
                # Create new scenario
                new_scenario = Scenario(
                    name=scenario_name,
                    company_id=company_id,
                    base=False,
                    params={
                        'description': scenario_description,
                        'scenario_type': scenario_type,
                        'created_from': 'ui'
                    }
                )
                
                session.add(new_scenario)
                session.commit()
                session.refresh(new_scenario)
                
                # Create adjusted assumptions
                for key, base_value in base_assumptions.items():
                    adjusted_value = base_value
                    
                    # Apply adjustments
                    if key == 'sales_growth':
                        adjusted_value = base_value + (sales_growth_adj / 100)
                    elif key == 'dso_days':
                        adjusted_value = base_value + dso_adj
                    elif key == 'opex_growth':
                        adjusted_value = base_value + (opex_growth_adj / 100)
                    elif key == 'variable_cost_ratio':
                        adjusted_value = base_value + (variable_cost_adj / 100)
                    elif key == 'capex_monthly':
                        adjusted_value = base_value + capex_adj
                    
                    # Apply market risk factors
                    if key in ['sales_growth'] and market_risk > 0:
                        adjusted_value = adjusted_value * (1 - market_risk)
                    
                    if key in ['opex_growth'] and inflation_factor > 0:
                        adjusted_value = adjusted_value + (inflation_factor / 100 / 12)  # Monthly inflation
                    
                    # Create assumption record
                    assumption = Assumption(
                        company_id=company_id,
                        scenario_id=new_scenario.id,
                        key=key,
                        value=adjusted_value
                    )
                    session.add(assumption)
                
                session.commit()
                display_success_message(f"Scenario '{scenario_name}' created successfully!")
                st.rerun()
                
            except Exception as e:
                session.rollback()
                display_error_message("Failed to create scenario", str(e))

def handle_manage_scenarios(session: Session, company_id: int):
    """Handle scenario management."""
    st.markdown("### ⚙️ Manage Scenarios")
    
    scenarios = session.exec(
        select(Scenario).where(Scenario.company_id == company_id)
    ).all()
    
    if not scenarios:
        st.info("No scenarios found. Create your first scenario in the 'Create Scenario' tab.")
        return
    
    # Display scenarios table
    scenario_data = []
    for scenario in scenarios:
        scenario_data.append({
            'ID': scenario.id,
            'Name': scenario.name,
            'Type': '🎯 Base' if scenario.base else '🧪 Custom',
            'Created': scenario.created_at.strftime('%Y-%m-%d'),
            'Description': scenario.params.get('description', '')[:50] + '...' if scenario.params.get('description', '') else 'No description'
        })
    
    import pandas as pd
    df = pd.DataFrame(scenario_data)
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Scenario actions
    st.markdown("#### 🔧 Scenario Actions")
    
    selected_scenario_name = st.selectbox(
        "Select scenario",
        options=[s.name for s in scenarios if not s.base],  # Don't allow base scenario deletion
        help="Select a scenario to edit or delete"
    )
    
    if selected_scenario_name:
        selected_scenario = next(s for s in scenarios if s.name == selected_scenario_name)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 Edit Assumptions", use_container_width=True):
                st.info("Edit functionality would allow modifying scenario assumptions")
        
        with col2:
            if st.button("📋 Duplicate", use_container_width=True):
                try:
                    # Create duplicate scenario
                    new_name = f"{selected_scenario.name} (Copy)"
                    
                    duplicate = Scenario(
                        name=new_name,
                        company_id=company_id,
                        base=False,
                        params=selected_scenario.params.copy()
                    )
                    
                    session.add(duplicate)
                    session.commit()
                    session.refresh(duplicate)
                    
                    # Copy assumptions
                    original_assumptions = session.exec(
                        select(Assumption).where(
                            Assumption.scenario_id == selected_scenario.id
                        )
                    ).all()
                    
                    for assumption in original_assumptions:
                        new_assumption = Assumption(
                            company_id=company_id,
                            scenario_id=duplicate.id,
                            key=assumption.key,
                            value=assumption.value
                        )
                        session.add(new_assumption)
                    
                    session.commit()
                    display_success_message(f"Scenario duplicated as '{new_name}'")
                    st.rerun()
                    
                except Exception as e:
                    session.rollback()
                    display_error_message("Failed to duplicate scenario", str(e))
        
        with col3:
            if st.button("🗑️ Delete", use_container_width=True, type="secondary"):
                # Confirmation dialog
                if st.checkbox(f"Confirm deletion of '{selected_scenario_name}'"):
                    try:
                        # Delete associated assumptions first
                        assumptions = session.exec(
                            select(Assumption).where(
                                Assumption.scenario_id == selected_scenario.id
                            )
                        ).all()
                        
                        for assumption in assumptions:
                            session.delete(assumption)
                        
                        # Delete scenario
                        session.delete(selected_scenario)
                        session.commit()
                        
                        display_success_message("Scenario deleted successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        session.rollback()
                        display_error_message("Failed to delete scenario", str(e))

def get_scenario_assumptions(session: Session, company_id: int, scenario_id: int) -> Dict[str, float]:
    """Get assumptions for a scenario."""
    assumptions = {}
    assumptions.update(DEFAULT_ASSUMPTIONS)
    
    db_assumptions = session.exec(
        select(Assumption).where(
            Assumption.company_id == company_id,
            Assumption.scenario_id == scenario_id
        )
    ).all()
    
    for assumption in db_assumptions:
        assumptions[assumption.key] = assumption.value
    
    return assumptions

if __name__ == "__main__":
    main()