import io
from datetime import date, datetime
from typing import List, Dict, Optional
import pandas as pd
import xlsxwriter
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.lineplots import LinePlot
import plotly.graph_objects as go
import plotly.express as px
from src.core.schemas import CashFlowProjection, KPIMetrics
from src.core.utils import format_currency

class ExcelExporter:
    """Export cash flow data to Excel format."""
    
    def __init__(self):
        self.workbook = None
        self.worksheet = None
    
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
            'num_format': f'_({currency} * #,##0_);_({currency} * (#,##0);_({currency} * "-"_);_(@_)'
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

class PDFExporter:
    """Export cash flow data to PDF format."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue
        )
    
    def export_cash_flow_report(
        self,
        projections: List[CashFlowProjection],
        assumptions: Dict[str, float],
        kpis: KPIMetrics,
        company_name: str,
        currency: str = "USD"
    ) -> bytes:
        """Export complete cash flow report to PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph(f"{company_name}<br/>Cash Flow Analysis Report", self.title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Date
        date_para = Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", 
                             self.styles['Normal'])
        story.append(date_para)
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['Heading2']))
        
        summary_text = f"""
        This report presents a 24-month cash flow projection for {company_name}. 
        Key findings include a minimum cash position of {format_currency(kpis.min_cash, currency)} 
        occurring in {kpis.min_cash_month.strftime('%B %Y')}, and a final projected cash position 
        of {format_currency(kpis.final_cash, currency)}.
        """
        
        if kpis.months_of_runway:
            summary_text += f" The company has approximately {kpis.months_of_runway} months of runway based on current burn rate."
        
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Key Metrics Table
        story.append(Paragraph("Key Performance Indicators", self.styles['Heading2']))
        
        kpi_data = [
            ['Metric', 'Value'],
            ['Minimum Cash Position', format_currency(kpis.min_cash, currency)],
            ['Month of Minimum Cash', kpis.min_cash_month.strftime('%B %Y')],
            ['Months of Runway', str(kpis.months_of_runway) if kpis.months_of_runway else 'N/A'],
            ['Average Monthly Burn Rate', format_currency(kpis.avg_burn_rate, currency)],
            ['DSCR (if applicable)', f"{kpis.dscr:.2f}" if kpis.dscr else 'N/A'],
            ['Final Cash Position', format_currency(kpis.final_cash, currency)]
        ]
        
        kpi_table = Table(kpi_data, colWidths=[3*inch, 2*inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(kpi_table)
        story.append(Spacer(1, 20))
        
        # Assumptions
        story.append(Paragraph("Key Assumptions", self.styles['Heading2']))
        
        assumption_labels = {
            'sales_growth': 'Monthly Sales Growth Rate',
            'dso_days': 'Days Sales Outstanding',
            'dpo_days': 'Days Payable Outstanding',
            'tax_rate': 'Tax Rate',
            'capex_monthly': 'Monthly CapEx',
            'interest_rate': 'Annual Interest Rate'
        }
        
        assumption_data = [['Assumption', 'Value']]
        for key, label in assumption_labels.items():
            value = assumptions.get(key, 0)
            if key in ['sales_growth', 'tax_rate', 'interest_rate']:
                formatted_value = f"{value:.2%}"
            elif key in ['capex_monthly']:
                formatted_value = format_currency(value, currency)
            else:
                formatted_value = f"{value:.0f} days" if 'days' in label else str(value)
            
            assumption_data.append([label, formatted_value])
        
        assumption_table = Table(assumption_data, colWidths=[3*inch, 2*inch])
        assumption_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(assumption_table)
        story.append(Spacer(1, 20))
        
        # 12-Month Summary Table (abbreviated)
        story.append(Paragraph("12-Month Cash Flow Summary", self.styles['Heading2']))
        
        cf_data = [['Month', 'Cash In', 'Cash Out', 'Net Cash', 'Cumulative']]
        for projection in projections[:12]:  # First 12 months only
            cf_data.append([
                projection.month.strftime('%b %Y'),
                format_currency(projection.cash_in, currency),
                format_currency(projection.cash_out, currency),
                format_currency(projection.net_cash, currency),
                format_currency(projection.cumulative_cash, currency)
            ])
        
        cf_table = Table(cf_data, colWidths=[1*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.4*inch])
        cf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(cf_table)
        
        doc.build(story)
        buffer.seek(0)
        
        return buffer.getvalue()

def create_cash_flow_chart(projections: List[CashFlowProjection]) -> go.Figure:
    """Create interactive cash flow chart using Plotly."""
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
        line=dict(color='blue', width=3),
        marker=dict(size=6)
    ))
    
    # Net cash flow bars
    colors = ['green' if x > 0 else 'red' for x in net_cash]
    fig.add_trace(go.Bar(
        x=months,
        y=net_cash,
        name='Net Cash Flow',
        marker_color=colors,
        opacity=0.6,
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Cash Flow Projection',
        xaxis_title='Month',
        yaxis=dict(
            title='Cumulative Cash ($)',
            side='left'
        ),
        yaxis2=dict(
            title='Net Cash Flow ($)',
            side='right',
            overlaying='y'
        ),
        hovermode='x unified',
        legend=dict(x=0.01, y=0.99),
        template='plotly_white'
    )
    
    return fig