import streamlit as st
from datetime import date, datetime
from sqlmodel import Session
from src.auth.auth import require_auth, get_current_company_id
from src.core.db import get_session
from src.core.logic import CashFlowEngine
from src.core.models import Company, Scenario
from src.core.exporters import ExcelExporter, PDFExporter
from src.ui.components import display_success_message, display_error_message

st.set_page_config(page_title="Reports", page_icon="📊", layout="wide")

def main():
    if not require_auth():
        return
    
    st.title("📊 Reportes")
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
        
        st.markdown(f"### 🏢 {company.name} - Reports & Exports")
        
        # Tabs for different report types
        tab1, tab2, tab3 = st.tabs(["📈 Cash Flow Reports", "🧪 Scenario Reports", "📋 Custom Reports"])
        
        with tab1:
            handle_cashflow_reports(session, company_id, company)
        
        with tab2:
            handle_scenario_reports(session, company_id, company)
        
        with tab3:
            handle_custom_reports(session, company_id, company)

def handle_cashflow_reports(session: Session, company_id: int, company):
    """Handle standard cash flow reports."""
    st.markdown("### 📈 Cash Flow Reports")
    
    # Report configuration
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### ⚙️ Report Settings")
        
        projection_months = st.selectbox(
            "Projection Period",
            options=[12, 18, 24, 36],
            index=2,
            format_func=lambda x: f"{x} months"
        )
        
        include_assumptions = st.checkbox("Include Assumptions", value=True)
        include_kpis = st.checkbox("Include KPIs", value=True)
        include_charts = st.checkbox("Include Charts (PDF only)", value=True)
        
        report_title = st.text_input(
            "Report Title",
            value=f"{company.name} - Cash Flow Analysis",
            help="Custom title for the report"
        )
        
        # Generate reports
        if st.button("📊 Generate Reports", type="primary"):
            with st.spinner("Generating cash flow reports..."):
                try:
                    engine = CashFlowEngine(session, company_id)
                    projections = engine.project_cash_flow(months=projection_months)
                    kpis = engine.calculate_kpis(projections)
                    assumptions = engine.get_assumptions() if include_assumptions else {}
                    
                    st.session_state['report_data'] = {
                        'projections': projections,
                        'kpis': kpis,
                        'assumptions': assumptions,
                        'company': company,
                        'title': report_title
                    }
                    
                    display_success_message("Reports generated successfully!")
                    
                except Exception as e:
                    display_error_message("Failed to generate reports", str(e))
    
    with col2:
        st.markdown("#### 📄 Available Reports")
        
        if 'report_data' in st.session_state:
            data = st.session_state['report_data']
            
            # Excel Report
            st.markdown("##### 📊 Excel Report")
            st.write("Comprehensive financial analysis with multiple worksheets:")
            st.write("• Cash Flow Projections")
            st.write("• Key Performance Indicators") 
            st.write("• Business Assumptions")
            
            if st.button("📥 Download Excel Report", use_container_width=True):
                try:
                    exporter = ExcelExporter()
                    excel_data = exporter.export_cash_flow_report(
                        data['projections'],
                        data['assumptions'],
                        data['kpis'],
                        data['company'].name,
                        data['company'].base_currency
                    )
                    
                    filename = f"cashflow_report_{data['company'].name.replace(' ', '_').lower()}_{date.today().strftime('%Y%m%d')}.xlsx"
                    
                    st.download_button(
                        label="💾 Download Excel",
                        data=excel_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    display_error_message("Excel export failed", str(e))
            
            st.markdown("---")
            
            # PDF Report
            st.markdown("##### 📄 PDF Report")
            st.write("Executive summary report perfect for sharing:")
            st.write("• Executive Summary")
            st.write("• Key Metrics Dashboard")
            st.write("• 12-Month Projection Summary")
            
            if st.button("📥 Download PDF Report", use_container_width=True):
                try:
                    exporter = PDFExporter()
                    pdf_data = exporter.export_cash_flow_report(
                        data['projections'],
                        data['assumptions'],
                        data['kpis'],
                        data['company'].name,
                        data['company'].base_currency
                    )
                    
                    filename = f"cashflow_report_{data['company'].name.replace(' ', '_').lower()}_{date.today().strftime('%Y%m%d')}.pdf"
                    
                    st.download_button(
                        label="💾 Download PDF",
                        data=pdf_data,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    display_error_message("PDF export failed", str(e))
            
            st.markdown("---")
            
            # CSV Export
            st.markdown("##### 📋 CSV Data Export")
            st.write("Raw data for custom analysis:")
            
            if st.button("📥 Download CSV Data", use_container_width=True):
                try:
                    import pandas as pd
                    
                    # Convert projections to DataFrame
                    df_data = []
                    for p in data['projections']:
                        df_data.append({
                            'Month': p.month.strftime('%Y-%m'),
                            'Cash_In': p.cash_in,
                            'Cash_Out': p.cash_out,
                            'Net_Cash': p.net_cash,
                            'Cumulative_Cash': p.cumulative_cash
                        })
                    
                    df = pd.DataFrame(df_data)
                    csv_data = df.to_csv(index=False)
                    
                    filename = f"cashflow_data_{data['company'].name.replace(' ', '_').lower()}_{date.today().strftime('%Y%m%d')}.csv"
                    
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv_data,
                        file_name=filename,
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    display_error_message("CSV export failed", str(e))
        
        else:
            st.info("👈 Configure report settings and click 'Generate Reports' to create downloadable reports.")
            
            # Show sample report preview
            st.markdown("##### 📋 Report Preview")
            st.write("Your reports will include:")
            
            preview_data = {
                "📊 Excel Report": [
                    "Monthly cash flow projections (24 months)",
                    "Key performance indicators",
                    "Business assumptions and drivers",
                    "Multiple formatted worksheets"
                ],
                "📄 PDF Report": [
                    "Executive summary",
                    "Key metrics dashboard", 
                    "12-month projection table",
                    "Professional formatting"
                ],
                "📋 CSV Data": [
                    "Raw projection data",
                    "Monthly cash flows",
                    "Compatible with Excel/Google Sheets",
                    "Custom analysis ready"
                ]
            }
            
            for report_type, features in preview_data.items():
                with st.expander(report_type):
                    for feature in features:
                        st.write(f"• {feature}")

def handle_scenario_reports(session: Session, company_id: int, company):
    """Handle scenario comparison reports."""
    st.markdown("### 🧪 Scenario Comparison Reports")
    
    # Get available scenarios
    from sqlmodel import select
    scenarios = session.exec(
        select(Scenario).where(Scenario.company_id == company_id)
    ).all()
    
    if len(scenarios) < 2:
        st.warning("You need at least 2 scenarios to generate comparison reports.")
        return
    
    # Scenario selection
    scenario_options = {s.name: s.id for s in scenarios}
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### ⚙️ Comparison Settings")
        
        selected_scenarios = st.multiselect(
            "Select scenarios to compare",
            options=list(scenario_options.keys()),
            default=list(scenario_options.keys())[:3],
            help="Select 2-4 scenarios for comparison"
        )
        
        comparison_months = st.selectbox(
            "Comparison Period",
            options=[12, 18, 24],
            index=2,
            format_func=lambda x: f"{x} months"
        )
        
        include_risk_analysis = st.checkbox("Include Risk Analysis", value=True)
        include_sensitivity = st.checkbox("Include Sensitivity Analysis", value=False)
        
        if st.button("📊 Generate Scenario Report", type="primary"):
            if len(selected_scenarios) < 2:
                st.error("Please select at least 2 scenarios.")
            else:
                with st.spinner("Generating scenario comparison..."):
                    try:
                        engine = CashFlowEngine(session, company_id)
                        
                        scenario_results = []
                        for scenario_name in selected_scenarios:
                            scenario_id = scenario_options[scenario_name]
                            projections = engine.project_cash_flow(scenario_id, months=comparison_months)
                            kpis = engine.calculate_kpis(projections)
                            assumptions = engine.get_assumptions(scenario_id)
                            
                            scenario_results.append({
                                'scenario_name': scenario_name,
                                'projections': projections,
                                'kpis': kpis,
                                'assumptions': assumptions
                            })
                        
                        st.session_state['scenario_report_data'] = {
                            'scenarios': scenario_results,
                            'company': company,
                            'comparison_months': comparison_months,
                            'include_risk_analysis': include_risk_analysis
                        }
                        
                        display_success_message("Scenario report generated successfully!")
                        
                    except Exception as e:
                        display_error_message("Failed to generate scenario report", str(e))
    
    with col2:
        st.markdown("#### 📄 Scenario Reports")
        
        if 'scenario_report_data' in st.session_state:
            data = st.session_state['scenario_report_data']
            
            # Scenario comparison Excel
            st.markdown("##### 📊 Scenario Comparison Excel")
            st.write("Multi-scenario analysis with:")
            st.write(f"• {len(data['scenarios'])} scenario comparison")
            st.write("• Side-by-side projections")
            st.write("• KPI comparison matrix")
            st.write("• Risk analysis (if selected)")
            
            if st.button("📥 Download Scenario Excel", use_container_width=True):
                st.info("Scenario Excel export functionality would be implemented here")
            
            st.markdown("---")
            
            # Quick comparison table
            st.markdown("##### 📋 Quick Comparison")
            
            comparison_data = []
            for scenario in data['scenarios']:
                kpis = scenario['kpis']
                comparison_data.append({
                    'Scenario': scenario['scenario_name'],
                    'Final Cash': f"{company.base_currency} {kpis.final_cash:,.0f}",
                    'Min Cash': f"{company.base_currency} {kpis.min_cash:,.0f}",
                    'Runway': f"{kpis.months_of_runway} months" if kpis.months_of_runway else "N/A"
                })
            
            import pandas as pd
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        else:
            st.info("👈 Configure comparison settings to generate scenario reports.")

def handle_custom_reports(session: Session, company_id: int, company):
    """Handle custom report generation."""
    st.markdown("### 📋 Custom Reports")
    
    st.info("🚧 **Coming Soon**: Custom report builder with:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📊 Custom Metrics**
        - Select specific KPIs to include
        - Custom date ranges
        - Department-specific views
        - Custom calculations
        """)
        
        st.markdown("""
        **🎨 Formatting Options**
        - Custom branding/logos
        - Color schemes
        - Report templates
        - Multiple output formats
        """)
    
    with col2:
        st.markdown("""
        **📈 Advanced Analytics**
        - Trend analysis
        - Variance reporting
        - Rolling forecasts
        - Benchmark comparisons
        """)
        
        st.markdown("""
        **🔄 Automated Reports**
        - Scheduled generation
        - Email delivery
        - Dashboard integration
        - API exports
        """)
    
    st.markdown("---")
    
    # Quick custom export options
    st.markdown("#### 🔧 Quick Custom Exports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 KPIs Only", use_container_width=True):
            try:
                engine = CashFlowEngine(session, company_id)
                projections = engine.project_cash_flow(months=12)
                kpis = engine.calculate_kpis(projections)
                
                kpi_data = {
                    'Metric': [
                        'Final Cash Position',
                        'Minimum Cash Position', 
                        'Months of Runway',
                        'Average Burn Rate',
                        'DSCR'
                    ],
                    'Value': [
                        f"{company.base_currency} {kpis.final_cash:,.0f}",
                        f"{company.base_currency} {kpis.min_cash:,.0f}",
                        f"{kpis.months_of_runway} months" if kpis.months_of_runway else "N/A",
                        f"{company.base_currency} {kpis.avg_burn_rate:,.0f}",
                        f"{kpis.dscr:.2f}" if kpis.dscr else "N/A"
                    ]
                }
                
                import pandas as pd
                df = pd.DataFrame(kpi_data)
                csv_data = df.to_csv(index=False)
                
                st.download_button(
                    label="💾 Download KPIs CSV",
                    data=csv_data,
                    file_name=f"kpis_{company.name.replace(' ', '_').lower()}_{date.today().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                display_error_message("KPI export failed", str(e))
    
    with col2:
        if st.button("📈 12M Summary", use_container_width=True):
            try:
                engine = CashFlowEngine(session, company_id)
                projections = engine.project_cash_flow(months=12)
                
                summary_data = []
                for p in projections:
                    summary_data.append({
                        'Month': p.month.strftime('%b %Y'),
                        'Net Cash Flow': p.net_cash,
                        'Cumulative Cash': p.cumulative_cash
                    })
                
                import pandas as pd
                df = pd.DataFrame(summary_data)
                csv_data = df.to_csv(index=False)
                
                st.download_button(
                    label="💾 Download 12M CSV",
                    data=csv_data,
                    file_name=f"12m_summary_{company.name.replace(' ', '_').lower()}_{date.today().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                display_error_message("Summary export failed", str(e))
    
    with col3:
        if st.button("⚙️ Assumptions", use_container_width=True):
            try:
                engine = CashFlowEngine(session, company_id)
                assumptions = engine.get_assumptions()
                
                assumptions_data = []
                for key, value in assumptions.items():
                    assumptions_data.append({
                        'Assumption': key.replace('_', ' ').title(),
                        'Value': value
                    })
                
                import pandas as pd
                df = pd.DataFrame(assumptions_data)
                csv_data = df.to_csv(index=False)
                
                st.download_button(
                    label="💾 Download Assumptions CSV",
                    data=csv_data,
                    file_name=f"assumptions_{company.name.replace(' ', '_').lower()}_{date.today().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                display_error_message("Assumptions export failed", str(e))

if __name__ == "__main__":
    main()