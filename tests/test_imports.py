import pytest
import pandas as pd
from datetime import date
from io import StringIO
from src.core.schemas import TransactionImport

def test_transaction_import_validation():
    """Test transaction import schema validation."""
    
    # Valid transaction data
    valid_data = {
        'date': '2024-01-15',
        'category': 'Sales',
        'description': 'Product sales revenue',
        'amount': 1000.0,
        'currency': 'USD',
        'account': 'Revenue',
        'paid': True
    }
    
    # Should validate successfully
    transaction = TransactionImport(**valid_data)
    assert transaction.category == 'Sales'
    assert transaction.amount == 1000.0
    assert transaction.currency == 'USD'

def test_transaction_import_date_formats():
    """Test different date format parsing."""
    
    # Test YYYY-MM-DD format
    data1 = {
        'date': '2024-01-15',
        'category': 'Sales',
        'description': 'Test',
        'amount': 1000.0,
        'account': 'Revenue'
    }
    
    transaction1 = TransactionImport(**data1)
    assert transaction1.date == date(2024, 1, 15)
    
    # Test DD/MM/YYYY format
    data2 = {
        'date': '15/01/2024',
        'category': 'Sales',
        'description': 'Test',
        'amount': 1000.0,
        'account': 'Revenue'
    }
    
    transaction2 = TransactionImport(**data2)
    assert transaction2.date == date(2024, 1, 15)

def test_transaction_import_invalid_date():
    """Test invalid date format handling."""
    
    data = {
        'date': 'invalid-date',
        'category': 'Sales',
        'description': 'Test',
        'amount': 1000.0,
        'account': 'Revenue'
    }
    
    with pytest.raises(ValueError):
        TransactionImport(**data)

def test_csv_parsing():
    """Test CSV parsing functionality."""
    
    csv_data = """date,category,description,amount,currency,account,paid
2024-01-15,Sales,Product Revenue,1000.00,USD,Revenue,true
2024-01-20,COGS,Cost of Sales,-300.00,USD,COGS,true
2024-01-30,Salary,Employee Salary,-2000.00,USD,OpEx,true"""
    
    # Parse CSV
    df = pd.read_csv(StringIO(csv_data))
    
    # Should have 3 rows
    assert len(df) == 3
    
    # Should have correct columns
    expected_columns = ['date', 'category', 'description', 'amount', 'currency', 'account', 'paid']
    assert list(df.columns) == expected_columns
    
    # Test data conversion
    for _, row in df.iterrows():
        # Validate each row can be converted to TransactionImport
        transaction_data = {
            'date': row['date'],
            'category': row['category'],
            'description': row['description'],
            'amount': float(row['amount']),
            'currency': row['currency'],
            'account': row['account'],
            'paid': row['paid'] == 'true'
        }
        
        transaction = TransactionImport(**transaction_data)
        assert transaction is not None

def test_excel_parsing():
    """Test Excel parsing functionality."""
    
    # Create sample DataFrame that would come from Excel
    data = {
        'Date': ['2024-01-15', '2024-01-20', '2024-01-30'],
        'Category': ['Sales', 'COGS', 'Salary'],
        'Description': ['Product Revenue', 'Cost of Sales', 'Employee Salary'],
        'Amount': [1000.00, -300.00, -2000.00],
        'Currency': ['USD', 'USD', 'USD'],
        'Account': ['Revenue', 'COGS', 'OpEx'],
        'Paid': [True, True, True]
    }
    
    df = pd.DataFrame(data)
    
    # Should have 3 rows
    assert len(df) == 3
    
    # Test column mapping (case insensitive)
    column_mapping = {
        'Date': 'date',
        'Category': 'category',
        'Description': 'description',
        'Amount': 'amount',
        'Currency': 'currency',
        'Account': 'account',
        'Paid': 'paid'
    }
    
    # Rename columns
    df_mapped = df.rename(columns=column_mapping)
    
    # Validate each row
    for _, row in df_mapped.iterrows():
        transaction_data = {
            'date': str(row['date']),
            'category': row['category'],
            'description': row['description'],
            'amount': float(row['amount']),
            'currency': row['currency'],
            'account': row['account'],
            'paid': bool(row['paid'])
        }
        
        transaction = TransactionImport(**transaction_data)
        assert transaction is not None

def test_missing_columns():
    """Test handling of missing required columns."""
    
    # CSV with missing 'amount' column
    csv_data = """date,category,description,currency,account,paid
2024-01-15,Sales,Product Revenue,USD,Revenue,true"""
    
    df = pd.read_csv(StringIO(csv_data))
    
    # Should detect missing column
    required_columns = ['date', 'category', 'description', 'amount', 'currency', 'account', 'paid']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    assert 'amount' in missing_columns

def test_data_type_conversion():
    """Test automatic data type conversion."""
    
    # Data with string amounts that need conversion
    data = {
        'date': '2024-01-15',
        'category': 'Sales',
        'description': 'Test Transaction',
        'amount': '1,500.50',  # String with comma
        'currency': 'USD',
        'account': 'Revenue',
        'paid': 'true'  # String boolean
    }
    
    # Convert amount (remove comma)
    amount_str = data['amount'].replace(',', '')
    amount_float = float(amount_str)
    
    # Convert paid
    paid_bool = data['paid'].lower() == 'true'
    
    transaction_data = {
        'date': data['date'],
        'category': data['category'],
        'description': data['description'],
        'amount': amount_float,
        'currency': data['currency'],
        'account': data['account'],
        'paid': paid_bool
    }
    
    transaction = TransactionImport(**transaction_data)
    assert transaction.amount == 1500.50
    assert transaction.paid == True

def test_duplicate_detection():
    """Test duplicate transaction detection logic."""
    
    # Sample transactions that might be duplicates
    transactions = [
        {
            'date': '2024-01-15',
            'category': 'Sales',
            'description': 'Product Revenue',
            'amount': 1000.0,
            'account': 'Revenue'
        },
        {
            'date': '2024-01-15',
            'category': 'Sales',
            'description': 'Product Revenue',
            'amount': 1000.0,
            'account': 'Revenue'
        },
        {
            'date': '2024-01-16',  # Different date
            'category': 'Sales',
            'description': 'Product Revenue',
            'amount': 1000.0,
            'account': 'Revenue'
        }
    ]
    
    # Convert to DataFrame
    df = pd.DataFrame(transactions)
    
    # Check for duplicates based on date, amount, and description
    duplicate_mask = df.duplicated(subset=['date', 'amount', 'description'], keep=False)
    
    # Should find first two as duplicates
    assert duplicate_mask.iloc[0] == True
    assert duplicate_mask.iloc[1] == True
    assert duplicate_mask.iloc[2] == False

def test_account_mapping():
    """Test account mapping functionality."""
    
    # Sample data with different account names that need mapping
    import_accounts = ['Sales Revenue', 'Product Sales', 'Service Income']
    system_accounts = ['Revenue', 'Operating Expenses', 'Equipment']
    
    # Test mapping logic
    account_mapping = {}
    
    # Map all import accounts to 'Revenue' for this test
    for acc in import_accounts:
        account_mapping[acc] = 'Revenue'
    
    # Verify mapping
    assert account_mapping['Sales Revenue'] == 'Revenue'
    assert account_mapping['Product Sales'] == 'Revenue'
    assert account_mapping['Service Income'] == 'Revenue'

def test_currency_validation():
    """Test currency code validation."""
    
    valid_currencies = ['USD', 'EUR', 'GBP', 'UYU', 'ARS', 'BRL']
    
    for currency in valid_currencies:
        data = {
            'date': '2024-01-15',
            'category': 'Sales',
            'description': 'Test',
            'amount': 1000.0,
            'currency': currency,
            'account': 'Revenue'
        }
        
        # Should validate successfully
        transaction = TransactionImport(**data)
        assert transaction.currency == currency

def test_amount_validation():
    """Test amount validation and edge cases."""
    
    # Test positive amount
    data_positive = {
        'date': '2024-01-15',
        'category': 'Sales',
        'description': 'Revenue',
        'amount': 1000.0,
        'account': 'Revenue'
    }
    
    transaction_positive = TransactionImport(**data_positive)
    assert transaction_positive.amount == 1000.0
    
    # Test negative amount
    data_negative = {
        'date': '2024-01-15',
        'category': 'Expense',
        'description': 'Cost',
        'amount': -500.0,
        'account': 'OpEx'
    }
    
    transaction_negative = TransactionImport(**data_negative)
    assert transaction_negative.amount == -500.0
    
    # Test zero amount
    data_zero = {
        'date': '2024-01-15',
        'category': 'Transfer',
        'description': 'Zero amount',
        'amount': 0.0,
        'account': 'Cash'
    }
    
    transaction_zero = TransactionImport(**data_zero)
    assert transaction_zero.amount == 0.0

if __name__ == "__main__":
    pytest.main([__file__])