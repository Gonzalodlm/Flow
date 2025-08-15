from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
from dateutil.relativedelta import relativedelta
import pandas as pd
from sqlmodel import Session, select
from src.core.models import (
    Company, Transaction, Account, Assumption, Scenario,
    AccountType, DEFAULT_ASSUMPTIONS
)
from src.core.schemas import CashFlowProjection, KPIMetrics
from src.core.utils import (
    get_month_start, get_months_range, safe_divide,
    calculate_working_capital_days, apply_growth_rate,
    get_quarter_from_date, is_quarter_end
)
from src.core.fx import FXManager

class CashFlowEngine:
    def __init__(self, session: Session, company_id: int):
        self.session = session
        self.company_id = company_id
        self.fx_manager = FXManager()
    
    def get_assumptions(self, scenario_id: Optional[int] = None) -> Dict[str, float]:
        """Get assumptions for a scenario or default values."""
        assumptions = {}
        
        # Start with defaults
        assumptions.update(DEFAULT_ASSUMPTIONS)
        
        # Override with company-specific assumptions
        query = select(Assumption).where(Assumption.company_id == self.company_id)
        
        if scenario_id:
            query = query.where(
                (Assumption.scenario_id == scenario_id) | 
                (Assumption.scenario_id.is_(None))
            )
        else:
            query = query.where(Assumption.scenario_id.is_(None))
        
        db_assumptions = self.session.exec(query).all()
        
        for assumption in db_assumptions:
            assumptions[assumption.key] = assumption.value
        
        return assumptions
    
    def get_historical_data(self, months_back: int = 12) -> pd.DataFrame:
        """Get historical transaction data for analysis."""
        end_date = date.today()
        start_date = end_date - relativedelta(months=months_back)
        
        query = select(Transaction).where(
            Transaction.company_id == self.company_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        
        transactions = self.session.exec(query).all()
        
        if not transactions:
            return pd.DataFrame()
        
        # Convert to DataFrame for analysis
        data = []
        for tx in transactions:
            data.append({
                'date': tx.date,
                'month': get_month_start(tx.date),
                'category': tx.category,
                'amount': tx.amount,
                'account_id': tx.account_id,
                'currency': tx.currency,
                'paid': tx.paid
            })
        
        df = pd.DataFrame(data)
        
        # Convert amounts to base currency
        company = self.session.get(Company, self.company_id)
        base_currency = company.base_currency if company else "USD"
        
        for idx, row in df.iterrows():
            if row['currency'] != base_currency:
                converted_amount = self.fx_manager.convert(
                    row['amount'], row['currency'], base_currency, row['date']
                )
                df.at[idx, 'amount'] = converted_amount
        
        return df
    
    def calculate_historical_averages(self) -> Dict[str, float]:
        """Calculate historical averages for projection."""
        df = self.get_historical_data()
        
        if df.empty:
            return {
                'monthly_revenue': 10000.0,
                'monthly_cogs': -3000.0,
                'monthly_opex': -5000.0,
                'monthly_capex': -500.0
            }
        
        # Group by month and category
        monthly_data = df.groupby(['month', 'category'])['amount'].sum().reset_index()
        
        # Calculate averages by category type
        revenue_categories = ['Sales', 'Revenue', 'Income']
        cogs_categories = ['COGS', 'Cost of Goods Sold', 'Direct Costs']
        opex_categories = ['Rent', 'Salaries', 'Payroll', 'Marketing', 'Operating Expenses']
        capex_categories = ['Equipment', 'CapEx', 'Capital Expenditure']
        
        def get_avg_for_categories(categories):
            mask = monthly_data['category'].isin(categories)
            if mask.any():
                return monthly_data[mask].groupby('month')['amount'].sum().mean()
            return 0.0
        
        return {
            'monthly_revenue': max(0, get_avg_for_categories(revenue_categories)),
            'monthly_cogs': min(0, get_avg_for_categories(cogs_categories)),
            'monthly_opex': min(0, get_avg_for_categories(opex_categories)),
            'monthly_capex': min(0, get_avg_for_categories(capex_categories))
        }
    
    def project_cash_flow(
        self, 
        scenario_id: Optional[int] = None,
        months: int = 24
    ) -> List[CashFlowProjection]:
        """Project cash flow for specified number of months."""
        assumptions = self.get_assumptions(scenario_id)
        historical_avgs = self.calculate_historical_averages()
        
        # Starting date is first day of current month
        start_date = get_month_start(date.today())
        projection_months = get_months_range(start_date, months)
        
        projections = []
        cumulative_cash = self._get_current_cash_position()
        
        for i, month_date in enumerate(projection_months):
            # Calculate revenue with growth
            base_revenue = historical_avgs['monthly_revenue']
            projected_revenue = apply_growth_rate(
                base_revenue, 
                assumptions['sales_growth'], 
                i
            )
            
            # Calculate cash inflows (considering DSO)
            cash_in = self._calculate_cash_inflows(
                projected_revenue, 
                assumptions['dso_days'], 
                i
            )
            
            # Calculate operating expenses with growth
            base_opex = abs(historical_avgs['monthly_opex'])
            projected_opex = apply_growth_rate(
                base_opex,
                assumptions.get('opex_growth', 0.02),
                i
            )
            
            # Calculate cash outflows (considering DPO)
            cogs_outflow = self._calculate_cogs_outflow(
                projected_revenue,
                assumptions['dpo_days'],
                historical_avgs['monthly_cogs']
            )
            
            opex_outflow = self._calculate_opex_outflow(
                projected_opex,
                assumptions['dpo_days']
            )
            
            capex_outflow = assumptions['capex_monthly']
            
            # Calculate debt service
            debt_service = self._calculate_debt_service(assumptions, i)
            
            # Calculate taxes (quarterly)
            tax_payment = self._calculate_tax_payment(
                projected_revenue + historical_avgs['monthly_cogs'],
                assumptions['tax_rate'],
                month_date
            )
            
            # Total cash flows
            total_cash_out = (
                abs(cogs_outflow) + 
                abs(opex_outflow) + 
                abs(capex_outflow) + 
                abs(debt_service) + 
                abs(tax_payment)
            )
            
            net_cash = cash_in - total_cash_out
            cumulative_cash += net_cash
            
            projections.append(CashFlowProjection(
                month=month_date,
                cash_in=cash_in,
                cash_out=total_cash_out,
                net_cash=net_cash,
                cumulative_cash=cumulative_cash
            ))
        
        return projections
    
    def _get_current_cash_position(self) -> float:
        """Get current cash position from transactions."""
        query = select(Transaction).where(
            Transaction.company_id == self.company_id,
            Transaction.paid == True
        )
        
        transactions = self.session.exec(query).all()
        
        total_cash = 0.0
        company = self.session.get(Company, self.company_id)
        base_currency = company.base_currency if company else "USD"
        
        for tx in transactions:
            amount = tx.amount
            if tx.currency != base_currency:
                amount = self.fx_manager.convert(
                    tx.amount, tx.currency, base_currency, tx.date
                )
            total_cash += amount
        
        return max(total_cash, 0.0)  # Assume minimum starting cash of 0
    
    def _calculate_cash_inflows(
        self, 
        revenue: float, 
        dso_days: float, 
        month_index: int
    ) -> float:
        """Calculate cash inflows considering DSO delays."""
        # Simple DSO model: cash collected this month is from sales made DSO days ago
        dso_months = dso_days / 30.0
        
        if month_index == 0:
            # First month: assume some cash from previous sales
            return revenue * (1 - dso_months + 0.5)
        elif month_index < dso_months:
            # Early months: partial collection
            return revenue * (month_index / dso_months)
        else:
            # Normal operations: full collection from previous period sales
            return revenue
    
    def _calculate_cogs_outflow(
        self, 
        revenue: float, 
        dpo_days: float, 
        historical_cogs_ratio: float
    ) -> float:
        """Calculate COGS outflow considering DPO delays."""
        cogs_amount = abs(revenue * (historical_cogs_ratio / historical_cogs_ratio if historical_cogs_ratio != 0 else 0.3))
        
        # DPO delay: we pay suppliers DPO days later
        dpo_factor = min(1.0, dpo_days / 30.0)
        return cogs_amount * (1 - dpo_factor * 0.3)  # Simplified DPO effect
    
    def _calculate_opex_outflow(self, opex_amount: float, dpo_days: float) -> float:
        """Calculate operating expense outflow."""
        # Most OpEx is paid promptly (salaries, rent)
        return opex_amount
    
    def _calculate_debt_service(self, assumptions: Dict[str, float], month_index: int) -> float:
        """Calculate debt service payments."""
        principal = assumptions.get('debt_principal', 0.0)
        annual_rate = assumptions.get('interest_rate', 0.0)
        term_months = assumptions.get('debt_term_months', 60)
        
        if principal <= 0:
            return 0.0
        
        monthly_rate = annual_rate / 12
        
        if monthly_rate > 0:
            # Calculate monthly payment (principal + interest)
            monthly_payment = principal * (
                monthly_rate * (1 + monthly_rate) ** term_months
            ) / ((1 + monthly_rate) ** term_months - 1)
        else:
            # No interest case
            monthly_payment = principal / term_months
        
        return monthly_payment if month_index < term_months else 0.0
    
    def _calculate_tax_payment(
        self, 
        operating_income: float, 
        tax_rate: float, 
        month_date: date
    ) -> float:
        """Calculate tax payments (quarterly)."""
        if not is_quarter_end(month_date) or operating_income <= 0:
            return 0.0
        
        # Quarterly tax payment on operating income
        quarterly_income = operating_income * 3  # Approximate quarterly income
        return quarterly_income * tax_rate
    
    def calculate_kpis(self, projections: List[CashFlowProjection]) -> KPIMetrics:
        """Calculate KPIs from cash flow projections."""
        if not projections:
            return KPIMetrics(
                min_cash=0.0,
                min_cash_month=date.today(),
                months_of_runway=None,
                avg_burn_rate=0.0,
                dscr=None,
                final_cash=0.0
            )
        
        # Find minimum cash and when it occurs
        min_projection = min(projections, key=lambda p: p.cumulative_cash)
        min_cash = min_projection.cumulative_cash
        min_cash_month = min_projection.month
        
        # Calculate months of runway (if burning cash)
        months_of_runway = None
        negative_months = [p for p in projections if p.net_cash < 0]
        
        if negative_months:
            avg_burn = abs(sum(p.net_cash for p in negative_months) / len(negative_months))
            current_cash = projections[0].cumulative_cash - projections[0].net_cash
            
            if avg_burn > 0:
                months_of_runway = int(current_cash / avg_burn)
        
        # Average burn rate
        negative_cash_flows = [p.net_cash for p in projections if p.net_cash < 0]
        avg_burn_rate = abs(sum(negative_cash_flows) / len(negative_cash_flows)) if negative_cash_flows else 0.0
        
        # DSCR calculation (simplified)
        assumptions = self.get_assumptions()
        debt_service = self._calculate_debt_service(assumptions, 0)
        
        operating_cash_flows = [p.net_cash + debt_service for p in projections[:12]]  # Exclude debt service from operating CF
        avg_operating_cf = sum(operating_cash_flows) / len(operating_cash_flows)
        
        dscr = safe_divide(avg_operating_cf, debt_service) if debt_service > 0 else None
        
        # Final cash position
        final_cash = projections[-1].cumulative_cash
        
        return KPIMetrics(
            min_cash=min_cash,
            min_cash_month=min_cash_month,
            months_of_runway=months_of_runway,
            avg_burn_rate=avg_burn_rate,
            dscr=dscr,
            final_cash=final_cash
        )
    
    def create_scenario_comparison(
        self, 
        scenario_ids: List[int], 
        months: int = 24
    ) -> List[Dict]:
        """Compare multiple scenarios."""
        comparisons = []
        
        for scenario_id in scenario_ids:
            scenario = self.session.get(Scenario, scenario_id)
            if not scenario or scenario.company_id != self.company_id:
                continue
            
            projections = self.project_cash_flow(scenario_id, months)
            kpis = self.calculate_kpis(projections)
            
            comparisons.append({
                'scenario_name': scenario.name,
                'projections': projections,
                'kpis': kpis
            })
        
        return comparisons