from datetime import date, datetime
from typing import Dict, Optional
import pandas as pd
from pathlib import Path
import csv

class FXManager:
    """Handle foreign exchange rates and conversions."""
    
    def __init__(self):
        self.rates_cache: Dict[str, Dict[str, float]] = {}
        self.data_file = Path(__file__).parent.parent.parent / "data" / "fx_rates_sample.csv"
        self._load_rates()
    
    def _load_rates(self):
        """Load exchange rates from CSV file."""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        date_str = row['date']
                        from_currency = row['from_currency']
                        to_currency = row['to_currency'] 
                        rate = float(row['rate'])
                        
                        if date_str not in self.rates_cache:
                            self.rates_cache[date_str] = {}
                        
                        pair_key = f"{from_currency}_{to_currency}"
                        self.rates_cache[date_str][pair_key] = rate
        except Exception as e:
            print(f"Warning: Could not load FX rates: {e}")
    
    def get_rate(
        self, 
        from_currency: str, 
        to_currency: str, 
        target_date: date
    ) -> float:
        """Get exchange rate for a specific date."""
        if from_currency == to_currency:
            return 1.0
        
        date_str = target_date.strftime('%Y-%m-%d')
        pair_key = f"{from_currency}_{to_currency}"
        reverse_pair_key = f"{to_currency}_{from_currency}"
        
        # Try exact date
        if date_str in self.rates_cache:
            if pair_key in self.rates_cache[date_str]:
                return self.rates_cache[date_str][pair_key]
            elif reverse_pair_key in self.rates_cache[date_str]:
                return 1.0 / self.rates_cache[date_str][reverse_pair_key]
        
        # Try to find closest date
        closest_rate = self._find_closest_rate(from_currency, to_currency, target_date)
        if closest_rate:
            return closest_rate
        
        # Fallback to hardcoded common rates
        return self._get_fallback_rate(from_currency, to_currency)
    
    def _find_closest_rate(
        self, 
        from_currency: str, 
        to_currency: str, 
        target_date: date
    ) -> Optional[float]:
        """Find the closest available rate to the target date."""
        pair_key = f"{from_currency}_{to_currency}"
        reverse_pair_key = f"{to_currency}_{from_currency}"
        
        target_datetime = datetime.combine(target_date, datetime.min.time())
        closest_date = None
        min_diff = float('inf')
        
        for date_str in self.rates_cache:
            try:
                rate_date = datetime.strptime(date_str, '%Y-%m-%d')
                diff = abs((target_datetime - rate_date).days)
                
                if diff < min_diff and (
                    pair_key in self.rates_cache[date_str] or 
                    reverse_pair_key in self.rates_cache[date_str]
                ):
                    min_diff = diff
                    closest_date = date_str
            except ValueError:
                continue
        
        if closest_date and min_diff <= 30:  # Within 30 days
            if pair_key in self.rates_cache[closest_date]:
                return self.rates_cache[closest_date][pair_key]
            elif reverse_pair_key in self.rates_cache[closest_date]:
                return 1.0 / self.rates_cache[closest_date][reverse_pair_key]
        
        return None
    
    def _get_fallback_rate(self, from_currency: str, to_currency: str) -> float:
        """Get fallback exchange rate for common currency pairs."""
        fallback_rates = {
            'USD_EUR': 0.85,
            'EUR_USD': 1.18,
            'USD_GBP': 0.75,
            'GBP_USD': 1.33,
            'USD_UYU': 40.0,
            'UYU_USD': 0.025,
            'EUR_GBP': 0.88,
            'GBP_EUR': 1.14,
            'USD_ARS': 350.0,
            'ARS_USD': 0.0029,
            'USD_BRL': 5.0,
            'BRL_USD': 0.20,
        }
        
        pair_key = f"{from_currency}_{to_currency}"
        
        if pair_key in fallback_rates:
            return fallback_rates[pair_key]
        
        # If no rate found, return 1.0 (no conversion)
        print(f"Warning: No exchange rate found for {from_currency} to {to_currency}, using 1.0")
        return 1.0
    
    def convert(
        self, 
        amount: float, 
        from_currency: str, 
        to_currency: str, 
        target_date: date
    ) -> float:
        """Convert amount from one currency to another."""
        if from_currency == to_currency:
            return amount
        
        rate = self.get_rate(from_currency, to_currency, target_date)
        return amount * rate
    
    def get_supported_currencies(self) -> list[str]:
        """Get list of supported currencies."""
        currencies = set()
        
        for date_rates in self.rates_cache.values():
            for pair_key in date_rates.keys():
                from_curr, to_curr = pair_key.split('_')
                currencies.add(from_curr)
                currencies.add(to_curr)
        
        # Add common currencies even if not in data
        currencies.update(['USD', 'EUR', 'GBP', 'UYU', 'ARS', 'BRL'])
        
        return sorted(list(currencies))
    
    def update_rate(
        self, 
        from_currency: str, 
        to_currency: str, 
        rate: float, 
        target_date: date
    ):
        """Manually update an exchange rate."""
        date_str = target_date.strftime('%Y-%m-%d')
        pair_key = f"{from_currency}_{to_currency}"
        
        if date_str not in self.rates_cache:
            self.rates_cache[date_str] = {}
        
        self.rates_cache[date_str][pair_key] = rate
        
        # Also store the reverse rate
        reverse_pair_key = f"{to_currency}_{from_currency}"
        self.rates_cache[date_str][reverse_pair_key] = 1.0 / rate
    
    def export_rates_to_csv(self, file_path: str):
        """Export current rates to CSV file."""
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['date', 'from_currency', 'to_currency', 'rate'])
            
            for date_str, rates in self.rates_cache.items():
                for pair_key, rate in rates.items():
                    from_curr, to_curr = pair_key.split('_')
                    writer.writerow([date_str, from_curr, to_curr, rate])

# Global FX manager instance
fx_manager = FXManager()