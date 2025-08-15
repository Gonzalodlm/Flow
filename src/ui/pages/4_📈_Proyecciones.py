import streamlit as st
import pandas as pd
from sqlmodel import Session
from src.auth.simple_auth import require_auth, get_current_company_id
from src.core.db import get_session
from src.core.logic import CashFlowEngine
from src.core.models import Company
from src.ui.components import (
    display_projections_table, create_cash_flow_chart,
    display_kpi_cards, display_error_message
)

st.set_page_config(page_title="Projections", page_icon="📈", layout="wide")

def main():
    if not require_auth():
        return
    
    st.title("📈 Proyecciones")
    st.markdown("---")
    
    company_id = get_current_company_id()
    if not company_id:
        st.error("No company selected.")
        return
    
    try:
        with next(get_session()) as session:
            company = session.get(Company, company_id)
            if not company:
                st.error("Company not found.")
                return
            
            st.markdown(f"### 🏢 {company.name} - Cash Flow Projections")
            
            # Projection parameters
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.markdown("#### ⚙️ Parameters")
                
                projection_months = st.selectbox(
                    "Projection Period",
                    options=[12, 18, 24, 36],
                    index=2,
                    format_func=lambda x: f"{x} months"
                )
                
                show_detailed = st.checkbox("Show Detailed Breakdown", value=False)
                
                if st.button("🔄 Refresh Projections", type="primary"):
                    st.rerun()
            
            with col2:
                # Initialize cash flow engine
                engine = CashFlowEngine(session, company_id)
                
                # Calculate projections
                with st.spinner("Calculating projections..."):
                    projections = engine.project_cash_flow(months=projection_months)
                    kpis = engine.calculate_kpis(projections)
                
                if not projections:
                    st.warning("No projections available. Please ensure you have:")
                    st.markdown("""
                    - Historical transaction data
                    - Configured business assumptions
                    - At least one account set up
                    """)
                    return
                
                # Display KPIs
                st.markdown("#### 📊 Key Metrics")
                display_kpi_cards(kpis, company.base_currency)
            
            st.markdown("---")
            
            # Main chart
            st.markdown("### 📊 Cash Flow Visualization")
            chart = create_cash_flow_chart(projections, company.base_currency)
            st.plotly_chart(chart, use_container_width=True)
            
            st.markdown("---")
            
            # Projections table
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### 📋 Detailed Projections")
                display_projections_table(projections, company.base_currency)
            
            with col2:
                st.markdown("### 💡 Insights")
                
                # Cash position analysis
                if kpis.min_cash < 0:
                    st.error(f"""
                    🚨 **Cash Flow Alert**
                    
                    Projected minimum cash position falls below zero:
                    - **Minimum**: {company.base_currency} {kpis.min_cash:,.0f}
                    - **Month**: {kpis.min_cash_month.strftime('%B %Y')}
                    
                    **Recommended Actions:**
                    - Accelerate collections (reduce DSO)
                    - Delay non-critical expenses
                    - Consider financing options
                    """)
                else:
                    st.success(f"""
                    ✅ **Positive Cash Flow**
                    
                    Cash position remains positive throughout the projection period.
                    """)
                
                # Runway analysis
                if kpis.months_of_runway:
                    if kpis.months_of_runway < 6:
                        st.error(f"""
                        ⏰ **Short Runway**
                        
                        Only {kpis.months_of_runway} months of runway remaining.
                        Consider immediate action to extend runway.
                        """)
                    elif kpis.months_of_runway < 12:
                        st.warning(f"""
                        🟡 **Moderate Runway**
                        
                        {kpis.months_of_runway} months of runway.
                        Plan for revenue growth or cost reduction.
                        """)
                    else:
                        st.info(f"""
                        ✅ **Sufficient Runway**
                        
                        {kpis.months_of_runway} months of runway available.
                        """)
                
                # DSCR analysis
                if kpis.dscr:
                    if kpis.dscr < 1.0:
                        st.error(f"""
                        📉 **DSCR Below 1.0**
                        
                        Current DSCR: {kpis.dscr:.2f}
                        
                        This indicates difficulty servicing debt.
                        """)
                    elif kpis.dscr < 1.25:
                        st.warning(f"""
                        🟡 **DSCR Concerns**
                        
                        Current DSCR: {kpis.dscr:.2f}
                        
                        Consider improving cash generation.
                        """)
                    else:
                        st.success(f"""
                        ✅ **Healthy DSCR**
                        
                        Current DSCR: {kpis.dscr:.2f}
                        
                        Debt service comfortably covered.
                        """)
                
                st.markdown("---")
                
                # Action recommendations
                st.markdown("#### 🎯 Recommendations")
                
                recommendations = []
                
                if kpis.avg_burn_rate > 0:
                    recommendations.append("Monitor burn rate closely")
                
                if kpis.min_cash < 50000:  # Arbitrary threshold
                    recommendations.append("Build cash reserves")
                
                # Always include growth recommendations
                recommendations.extend([
                    "Optimize working capital",
                    "Review pricing strategy",
                    "Monitor key assumptions monthly"
                ])
                
                for i, rec in enumerate(recommendations, 1):
                    st.write(f"{i}. {rec}")
            
            st.markdown("---")
            
            # Export options
            st.markdown("### 📤 Export Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Export to Excel", use_container_width=True):
                    # Generate Excel export
                    assumptions = engine.get_assumptions()
                    
                    from src.core.simple_exporters import SimpleExcelExporter
                    exporter = SimpleExcelExporter()
                    
                    excel_data = exporter.export_cash_flow_report(
                        projections, assumptions, kpis, 
                        company.name, company.base_currency
                    )
                    
                    st.download_button(
                        label="Download Excel Report",
                        data=excel_data,
                        file_name=f"cashflow_projection_{company.name.replace(' ', '_').lower()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            with col2:
                if st.button("📋 Export to CSV", use_container_width=True):
                    # Convert projections to DataFrame
                    df_data = []
                    for p in projections:
                        df_data.append({
                            'Month': p.month.strftime('%Y-%m'),
                            'Cash_In': p.cash_in,
                            'Cash_Out': p.cash_out,
                            'Net_Cash': p.net_cash,
                            'Cumulative_Cash': p.cumulative_cash
                        })
                    
                    df = pd.DataFrame(df_data)
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"cashflow_projection_{company.name.replace(' ', '_').lower()}.csv",
                        mime="text/csv"
                    )
            
            with col3:
                if st.button("📊 View Reports", use_container_width=True):
                    st.switch_page("src/ui/pages/6_📊_Reportes.py")
            
            # Show detailed breakdown if requested
            if show_detailed:
                st.markdown("---")
                st.markdown("### 🔍 Detailed Monthly Breakdown")
                
                # Create detailed DataFrame
                detailed_data = []
                assumptions = engine.get_assumptions()
                
                for p in projections:
                    detailed_data.append({
                        'Month': p.month.strftime('%b %Y'),
                        'Cash In': p.cash_in,
                        'Cash Out': p.cash_out,
                        'Net Cash': p.net_cash,
                        'Cumulative': p.cumulative_cash,
                        'Burn Rate': p.cash_out - p.cash_in if p.net_cash < 0 else 0,
                        'Growth Rate': assumptions.get('sales_growth', 0) * 100
                    })
                
                detailed_df = pd.DataFrame(detailed_data)
                
                # Format as currency
                currency_cols = ['Cash In', 'Cash Out', 'Net Cash', 'Cumulative', 'Burn Rate']
                for col in currency_cols:
                    detailed_df[col] = detailed_df[col].apply(lambda x: f"{company.base_currency} {x:,.0f}")
                
                detailed_df['Growth Rate'] = detailed_df['Growth Rate'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(detailed_df, use_container_width=True, hide_index=True)
    
    except Exception as e:
        display_error_message("Error generating projections", str(e))
        st.exception(e)

if __name__ == "__main__":
    main()