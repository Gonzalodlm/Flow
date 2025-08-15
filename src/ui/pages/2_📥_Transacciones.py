import streamlit as st
import pandas as pd
from datetime import date, datetime
from sqlmodel import Session, select
from src.auth.auth import require_auth, get_current_company_id
from src.core.db import get_session
from src.core.models import Transaction, Account, Company, AccountType, RecurrenceType
from src.ui.components import (
    display_transaction_upload, display_manual_transaction_form,
    display_success_message, display_error_message
)

st.set_page_config(page_title="Transactions", page_icon="📥", layout="wide")

def main():
    if not require_auth():
        return
    
    st.title("📥 Transacciones")
    st.markdown("---")
    
    company_id = get_current_company_id()
    if not company_id:
        st.error("No company selected.")
        return
    
    # Tabs for different transaction operations
    tab1, tab2, tab3 = st.tabs(["📁 Import Data", "✏️ Manual Entry", "📋 View Transactions"])
    
    with tab1:
        handle_import_tab(company_id)
    
    with tab2:
        handle_manual_entry_tab(company_id)
    
    with tab3:
        handle_view_transactions_tab(company_id)

def handle_import_tab(company_id: int):
    """Handle bulk import of transactions."""
    st.markdown("### 📁 Import Transactions from File")
    
    # Display upload interface
    display_transaction_upload()
    
    # Process uploaded transactions if available
    if 'uploaded_transactions' in st.session_state:
        df = st.session_state['uploaded_transactions']
        
        st.markdown("### 🔍 Review and Import")
        
        # Show data preview
        st.dataframe(df.head(10), use_container_width=True)
        
        # Account mapping
        with next(get_session()) as session:
            accounts = session.exec(
                select(Account).where(Account.company_id == company_id)
            ).all()
            
            if not accounts:
                st.error("No accounts found. Please create accounts first.")
                return
            
            account_options = {acc.name: acc.id for acc in accounts}
            
            # Map unique account names from uploaded data
            unique_accounts = df['account'].unique()
            
            st.markdown("### 🔗 Map Accounts")
            account_mapping = {}
            
            for acc_name in unique_accounts:
                account_mapping[acc_name] = st.selectbox(
                    f"Map '{acc_name}' to:",
                    options=list(account_options.keys()),
                    key=f"account_map_{acc_name}"
                )
            
            if st.button("📥 Import All Transactions", type="primary"):
                try:
                    imported_count = 0
                    
                    for _, row in df.iterrows():
                        # Map account
                        account_name = account_mapping.get(row['account'])
                        account_id = account_options.get(account_name)
                        
                        if not account_id:
                            continue
                        
                        # Parse date
                        if isinstance(row['date'], str):
                            try:
                                tx_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                            except ValueError:
                                tx_date = datetime.strptime(row['date'], '%d/%m/%Y').date()
                        else:
                            tx_date = row['date']
                        
                        # Create transaction
                        transaction = Transaction(
                            company_id=company_id,
                            date=tx_date,
                            account_id=account_id,
                            category=row['category'],
                            description=row['description'],
                            amount=float(row['amount']),
                            currency=row.get('currency', 'USD'),
                            paid=bool(row.get('paid', True)),
                            recurrence=RecurrenceType.NONE
                        )
                        
                        session.add(transaction)
                        imported_count += 1
                    
                    session.commit()
                    display_success_message(f"Imported {imported_count} transactions successfully!")
                    
                    # Clear session state
                    del st.session_state['uploaded_transactions']
                    st.rerun()
                    
                except Exception as e:
                    session.rollback()
                    display_error_message("Import failed", str(e))

def handle_manual_entry_tab(company_id: int):
    """Handle manual transaction entry."""
    st.markdown("### ✏️ Add Individual Transaction")
    
    with next(get_session()) as session:
        # Get accounts for dropdown
        accounts = session.exec(
            select(Account).where(Account.company_id == company_id)
        ).all()
        
        account_options = {acc.name: acc.id for acc in accounts}
        
        if not account_options:
            st.error("No accounts found. Please create accounts first in Admin section.")
            return
        
        with st.form("manual_transaction"):
            col1, col2 = st.columns(2)
            
            with col1:
                tx_date = st.date_input("Date", value=date.today())
                category = st.text_input(
                    "Category", 
                    placeholder="e.g., Sales, Rent, Salary",
                    help="Transaction category for grouping"
                )
                description = st.text_area(
                    "Description", 
                    placeholder="Detailed description of the transaction"
                )
                amount = st.number_input(
                    "Amount ($)", 
                    step=0.01, 
                    format="%.2f",
                    help="Positive for income, negative for expenses"
                )
            
            with col2:
                currency = st.selectbox(
                    "Currency", 
                    ["USD", "EUR", "GBP", "UYU", "ARS"], 
                    index=0
                )
                
                account_name = st.selectbox(
                    "Account", 
                    options=list(account_options.keys()),
                    help="Select the account this transaction belongs to"
                )
                
                paid = st.checkbox("Paid/Received", value=True)
                
                recurrence = st.selectbox(
                    "Recurrence", 
                    ["none", "monthly", "quarterly", "weekly"],
                    help="Select if this is a recurring transaction"
                )
                
                counterpart = st.text_input(
                    "Counterpart (Optional)",
                    placeholder="e.g., Customer name, Supplier",
                    help="Who you transacted with"
                )
            
            submitted = st.form_submit_button("💾 Add Transaction", type="primary")
            
            if submitted:
                if not category or not description or amount == 0:
                    st.error("Please fill in all required fields.")
                else:
                    try:
                        transaction = Transaction(
                            company_id=company_id,
                            date=tx_date,
                            account_id=account_options[account_name],
                            category=category,
                            description=description,
                            amount=amount,
                            currency=currency,
                            paid=paid,
                            recurrence=RecurrenceType(recurrence),
                            counterpart=counterpart if counterpart else None
                        )
                        
                        session.add(transaction)
                        session.commit()
                        
                        display_success_message("Transaction added successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        session.rollback()
                        display_error_message("Failed to add transaction", str(e))

def handle_view_transactions_tab(company_id: int):
    """Handle viewing and managing existing transactions."""
    st.markdown("### 📋 Transaction History")
    
    with next(get_session()) as session:
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            date_from = st.date_input("From Date", value=date(2024, 1, 1))
        
        with col2:
            date_to = st.date_input("To Date", value=date.today())
        
        with col3:
            # Get categories for filter
            categories = session.exec(
                select(Transaction.category).where(
                    Transaction.company_id == company_id
                ).distinct()
            ).all()
            
            selected_category = st.selectbox(
                "Category",
                ["All"] + list(categories),
                index=0
            )
        
        with col4:
            # Get accounts for filter
            accounts = session.exec(
                select(Account).where(Account.company_id == company_id)
            ).all()
            
            account_options = ["All"] + [acc.name for acc in accounts]
            selected_account = st.selectbox("Account", account_options, index=0)
        
        # Build query
        query = select(Transaction, Account).join(Account).where(
            Transaction.company_id == company_id,
            Transaction.date >= date_from,
            Transaction.date <= date_to
        )
        
        if selected_category != "All":
            query = query.where(Transaction.category == selected_category)
        
        if selected_account != "All":
            account_id = next(acc.id for acc in accounts if acc.name == selected_account)
            query = query.where(Transaction.account_id == account_id)
        
        # Get transactions
        results = session.exec(query).all()
        
        if not results:
            st.info("No transactions found for the selected criteria.")
            return
        
        # Convert to DataFrame for display
        df_data = []
        for transaction, account in results:
            df_data.append({
                'ID': transaction.id,
                'Date': transaction.date.strftime('%Y-%m-%d'),
                'Account': account.name,
                'Category': transaction.category,
                'Description': transaction.description,
                'Amount': transaction.amount,
                'Currency': transaction.currency,
                'Paid': '✅' if transaction.paid else '❌',
                'Counterpart': transaction.counterpart or '-'
            })
        
        df = pd.DataFrame(df_data)
        
        # Display summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Transactions", len(df))
        
        with col2:
            total_in = df[df['Amount'] > 0]['Amount'].sum()
            st.metric("Total Inflows", f"${total_in:,.2f}")
        
        with col3:
            total_out = abs(df[df['Amount'] < 0]['Amount'].sum())
            st.metric("Total Outflows", f"${total_out:,.2f}")
        
        with col4:
            net_amount = df['Amount'].sum()
            st.metric("Net Amount", f"${net_amount:,.2f}")
        
        st.markdown("---")
        
        # Display transactions table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Amount": st.column_config.NumberColumn(
                    "Amount",
                    format="$%.2f"
                )
            }
        )
        
        # Export options
        st.markdown("### 📤 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export to CSV", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"transactions_{date.today()}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("🗑️ Delete Selected", use_container_width=True, type="secondary"):
                st.warning("Delete functionality would be implemented here")

if __name__ == "__main__":
    main()