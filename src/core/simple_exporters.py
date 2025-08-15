import io
from datetime import date, datetime
from typing import List, Dict, Optional
import pandas as pd
import xlsxwriter
from src.core.schemas import CashFlowProjection, KPIMetrics
from src.core.utils import format_currency

class SimpleExcelExporter:
    """Simplified Excel exporter without external dependencies."""
    
    def export_cash_flow_report(
        self,
        projections: List[CashFlowProjection],
        assumptions: Dict[str, float],
        kpis: KPIMetrics,
        company_name: str,
        currency: str = "USD"
    ) -> bytes:
        """Export complete cash flow report to Excel."""
        output = io.BytesIO()
        
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#4472C4',
            'font_color': 'white'
        })
        
        subheader_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'left',
            'bg_color': '#D9E2F3'
        })
        
        currency_format = workbook.add_format({
            'num_format': f'${currency} #,##0.00'
        })
        
        percentage_format = workbook.add_format({
            'num_format': '0.00%'
        })
        
        date_format = workbook.add_format({
            'num_format': 'mmm yyyy'
        })
        
        # Create worksheets
        self._create_assumptions_sheet(workbook, assumptions, kpis, company_name, 
                                     subheader_format, currency_format, percentage_format)
        
        self._create_cashflow_sheet(workbook, projections, company_name, currency,
                                  header_format, subheader_format, currency_format, date_format)
        
        self._create_kpis_sheet(workbook, kpis, currency, 
                               subheader_format, currency_format)
        
        workbook.close()
        output.seek(0)
        
        return output.getvalue()
    
    def _create_assumptions_sheet(self, workbook, assumptions, kpis, company_name,
                                subheader_format, currency_format, percentage_format):
        """Create assumptions worksheet."""
        worksheet = workbook.add_worksheet('Assumptions')
        
        row = 0
        # Title
        worksheet.write(row, 0, f'{company_name} - Financial Assumptions', subheader_format)
        worksheet.write(row, 1, datetime.now().strftime('%Y-%m-%d'))
        row += 2
        
        # Key assumptions
        worksheet.write(row, 0, 'Key Assumptions', subheader_format)
        row += 1
        
        assumption_labels = {
            'sales_growth': 'Monthly Sales Growth Rate',
            'dso_days': 'Days Sales Outstanding',
            'dpo_days': 'Days Payable Outstanding',
            'tax_rate': 'Tax Rate',
            'capex_monthly': 'Monthly CapEx',
            'interest_rate': 'Annual Interest Rate',
            'min_cash_target': 'Minimum Cash Target',
            'debt_principal': 'Outstanding Debt Principal',
            'debt_term_months': 'Debt Term (Months)'
        }
        
        for key, label in assumption_labels.items():
            value = assumptions.get(key, 0)
            worksheet.write(row, 0, label)
            
            if key in ['sales_growth', 'tax_rate', 'interest_rate']:
                worksheet.write(row, 1, value, percentage_format)
            elif key in ['capex_monthly', 'min_cash_target', 'debt_principal']:
                worksheet.write(row, 1, value, currency_format)
            else:
                worksheet.write(row, 1, value)
            
            row += 1
        
        # Set column widths
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 15)
    
    def _create_cashflow_sheet(self, workbook, projections, company_name, currency,
                             header_format, subheader_format, currency_format, date_format):
        """Create cash flow projections worksheet."""
        worksheet = workbook.add_worksheet('Cash Flow Projection')
        
        row = 0
        # Title
        worksheet.write(row, 0, f'{company_name} - 24 Month Cash Flow Projection', subheader_format)
        row += 2
        
        # Headers
        headers = ['Month', 'Cash In', 'Cash Out', 'Net Cash Flow', 'Cumulative Cash']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, header_format)
        row += 1
        
        # Data
        for projection in projections:
            worksheet.write(row, 0, projection.month, date_format)
            worksheet.write(row, 1, projection.cash_in, currency_format)
            worksheet.write(row, 2, projection.cash_out, currency_format)
            worksheet.write(row, 3, projection.net_cash, currency_format)
            worksheet.write(row, 4, projection.cumulative_cash, currency_format)
            row += 1
        
        # Set column widths
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:E', 15)
    
    def _create_kpis_sheet(self, workbook, kpis, currency, subheader_format, currency_format):
        """Create KPIs worksheet."""
        worksheet = workbook.add_worksheet('Key Metrics')
        
        row = 0
        worksheet.write(row, 0, 'Key Performance Indicators', subheader_format)
        row += 2
        
        kpi_data = [
            ('Minimum Cash Position', kpis.min_cash, currency_format),
            ('Month of Minimum Cash', kpis.min_cash_month.strftime('%b %Y'), None),
            ('Months of Runway', kpis.months_of_runway or 'N/A', None),
            ('Average Burn Rate', kpis.avg_burn_rate, currency_format),
            ('DSCR (Debt Service Coverage)', kpis.dscr or 'N/A', None),
            ('Final Cash Position', kpis.final_cash, currency_format)
        ]
        
        for label, value, fmt in kpi_data:
            worksheet.write(row, 0, label)
            if fmt and isinstance(value, (int, float)):
                worksheet.write(row, 1, value, fmt)
            else:
                worksheet.write(row, 1, value)
            row += 1
        
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 15)