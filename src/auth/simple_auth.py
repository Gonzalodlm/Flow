import streamlit as st
import bcrypt
import yaml
from pathlib import Path
from typing import Optional, Dict

class SimpleAuth:
    """Simplified authentication without external dependencies."""
    
    def __init__(self):
        self.users_file = Path(__file__).parent / "users.yaml"
        self.users = self._load_users()
    
    def _load_users(self) -> Dict:
        """Load users from YAML file."""
        try:
            with open(self.users_file, 'r') as file:
                data = yaml.safe_load(file)
                return data.get('credentials', {}).get('usernames', {})
        except Exception:
            # Default users if file doesn't exist
            return {
                'admin': {
                    'email': 'admin@demo.com',
                    'name': 'Admin User',
                    'password': '$2b$12$gLH.eZpfvbFf9JoBFsKFOOKj9o.ktT9l6s9r2vNXY1mGNBq.8qE1y',
                    'company_id': 1,
                    'role': 'admin'
                },
                'analyst': {
                    'email': 'analyst@demo.com',
                    'name': 'Financial Analyst',
                    'password': '$2b$12$6kPhgKlFY1QTbYHwX7y4pOJy5zN9AzOUwFB0HvD1VR3Kd4L8PdD4K',
                    'company_id': 1,
                    'role': 'analyst'
                }
            }
    
    def check_password(self, username: str, password: str) -> bool:
        """Check if password is correct."""
        if username not in self.users:
            return False
        
        stored_password = self.users[username]['password']
        return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information."""
        if username in self.users:
            user = self.users[username].copy()
            user.pop('password', None)  # Remove password from response
            return user
        return None
    
    def login_form(self):
        """Display login form and handle authentication."""
        st.title("🔐 Cash Flow Analytics - Login")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if self.check_password(username, password):
                    user_info = self.get_user_info(username)
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_info = user_info
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        # Demo credentials info
        st.info("""
        **Demo Credentials:**
        - Admin: admin / admin123
        - Analyst: analyst / analyst123
        """)

def require_auth() -> bool:
    """Require authentication for protected pages."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        auth = SimpleAuth()
        auth.login_form()
        return False
    
    return True

def get_current_user() -> Optional[Dict]:
    """Get current user information."""
    return st.session_state.get('user_info')

def get_current_company_id() -> Optional[int]:
    """Get current company ID."""
    user_info = get_current_user()
    return user_info.get('company_id') if user_info else None

def is_admin() -> bool:
    """Check if current user is admin."""
    user_info = get_current_user()
    return user_info and user_info.get('role') == 'admin'

def logout():
    """Logout current user."""
    for key in ['authenticated', 'username', 'user_info']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def setup_sidebar():
    """Setup authentication sidebar."""
    user_info = get_current_user()
    
    if user_info:
        st.sidebar.write(f"👋 Welcome, {user_info['name']}")
        st.sidebar.write(f"📧 {user_info['email']}")
        st.sidebar.write(f"🏢 Company ID: {user_info['company_id']}")
        st.sidebar.write(f"👤 Role: {user_info['role'].title()}")
        
        if st.sidebar.button("🚪 Logout"):
            logout()
    else:
        st.sidebar.write("Please login to continue")