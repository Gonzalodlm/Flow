import streamlit as st
from datetime import date
from sqlmodel import Session
from src.auth.auth import require_auth, get_current_company_id
from src.core.db import get_session
from src.core.logic import CashFlowEngine
from src.core.models import Company
from src.ui.components import (
    display_kpi_cards, create_cash_flow_chart, 
    display_loading_spinner, display_error_message
)

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")

def main():
    if not require_auth():
        return
    
    st.title("🏠 Dashboard")
    st.markdown("---")
    
    company_id = get_current_company_id()
    if not company_id:
        st.error("No company selected. Please contact admin.")
        return
    
    try:
        with next(get_session()) as session:
            # Get company info
            company = session.get(Company, company_id)
            if not company:
                st.error("Company not found.")
                return
            
            st.markdown(f"### 🏢 {company.name}")
            st.markdown(f"**Base Currency:** {company.base_currency}")
            
            # Initialize cash flow engine
            engine = CashFlowEngine(session, company_id)
            
            # Calculate projections
            with st.spinner("Calculating cash flow projections..."):
                projections = engine.project_cash_flow(months=24)
                kpis = engine.calculate_kpis(projections)
            
            if not projections:
                st.warning("No projections available. Please import some transaction data first.")
                return
            
            # Display KPI cards
            st.markdown("### 📊 Key Performance Indicators")
            display_kpi_cards(kpis, company.base_currency)
            
            st.markdown("---")
            
            # Create two columns for charts
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### 📈 Cash Flow Projection")
                chart = create_cash_flow_chart(projections, company.base_currency)
                st.plotly_chart(chart, use_container_width=True)
            
            with col2:
                st.markdown("### 🎯 Key Metrics")
                
                # Cash position indicator
                current_cash = projections[0].cumulative_cash - projections[0].net_cash
                if current_cash < kpis.min_cash_target if hasattr(kpis, 'min_cash_target') else 10000:
                    st.error(f"💡 Cash position below target!")
                else:
                    st.success("💰 Cash position healthy")
                
                # Runway indicator
                if kpis.months_of_runway and kpis.months_of_runway < 6:
                    st.error(f"⚠️ Low runway: {kpis.months_of_runway} months")
                elif kpis.months_of_runway and kpis.months_of_runway < 12:
                    st.warning(f"🟡 Moderate runway: {kpis.months_of_runway} months")
                else:
                    st.success("✅ Sufficient runway")
                
                # DSCR indicator
                if kpis.dscr:
                    if kpis.dscr < 1.0:
                        st.error(f"📉 DSCR below 1.0: {kpis.dscr:.2f}")
                    elif kpis.dscr < 1.25:
                        st.warning(f"🟡 DSCR moderate: {kpis.dscr:.2f}")
                    else:
                        st.success(f"✅ DSCR healthy: {kpis.dscr:.2f}")
                
                st.markdown("---")
                
                # Quick actions
                st.markdown("### ⚡ Quick Actions")
                
                if st.button("📥 Import Transactions", use_container_width=True):
                    st.switch_page("src/ui/pages/2_📥_Transacciones.py")
                
                if st.button("⚙️ Update Assumptions", use_container_width=True):
                    st.switch_page("src/ui/pages/3_⚙️_Supuestos_y_Drivers.py")
                
                if st.button("🧪 Create Scenario", use_container_width=True):
                    st.switch_page("src/ui/pages/5_🧪_Escenarios.py")
                
                if st.button("📊 Generate Report", use_container_width=True):
                    st.switch_page("src/ui/pages/6_📊_Reportes.py")
            
            # Recent activity summary
            st.markdown("---")
            st.markdown("### 📋 Summary")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"""
                **Next 3 Months**
                - Average Net CF: ${sum(p.net_cash for p in projections[:3])/3:,.0f}
                - Min Cash: ${min(p.cumulative_cash for p in projections[:3]):,.0f}
                """)
            
            with col2:
                st.info(f"""
                **Next 12 Months**
                - Total Cash In: ${sum(p.cash_in for p in projections[:12]):,.0f}
                - Total Cash Out: ${sum(p.cash_out for p in projections[:12]):,.0f}
                """)
            
            with col3:
                st.info(f"""
                **Full Period (24M)**
                - Final Cash: ${kpis.final_cash:,.0f}
                - Min Position: ${kpis.min_cash:,.0f}
                """)
    
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()