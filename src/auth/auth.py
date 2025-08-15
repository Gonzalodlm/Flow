import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
from typing import Optional, Tuple
from src.core.db import get_session, get_user_by_email, get_companies_for_user
from src.core.models import User, Company

class AuthManager:
    def __init__(self):
        self.config_file = Path(__file__).parent / "users.yaml"
        self.authenticator = None
        self._load_config()
    
    def _load_config(self):
        """Load authentication configuration."""
        try:
            with open(self.config_file, 'r') as file:
                config = yaml.load(file, Loader=SafeLoader)
            
            self.authenticator = stauth.Authenticate(
                config['credentials'],
                config['cookie']['name'],
                config['cookie']['key'],
                config['cookie']['expiry_days'],
                config['preauthorized']
            )
        except Exception as e:
            st.error(f"Error loading authentication config: {e}")
            self.authenticator = None
    
    def login(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Handle login process."""
        if not self.authenticator:
            return None, None, None
        
        try:
            name, authentication_status, username = self.authenticator.login()
            return name, authentication_status, username
        except Exception as e:
            st.error(f"Login error: {e}")
            return None, None, None
    
    def logout(self):
        """Handle logout process."""
        if self.authenticator:
            self.authenticator.logout()
    
    def get_user_info(self, username: str) -> Optional[dict]:
        """Get user information from config."""
        try:
            with open(self.config_file, 'r') as file:
                config = yaml.load(file, Loader=SafeLoader)
            
            user_data = config['credentials']['usernames'].get(username)
            if user_data:
                return {
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'role': user_data.get('role', 'analyst'),
                    'company_id': user_data.get('company_id', 1)
                }
        except Exception as e:
            st.error(f"Error getting user info: {e}")
        return None

def require_auth() -> bool:
    """Decorator-like function to require authentication."""
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = None
    
    if 'authenticator' not in st.session_state:
        st.session_state.authenticator = AuthManager()
    
    if st.session_state.authentication_status != True:
        st.title("🔐 Cash Flow Analytics - Login")
        
        name, authentication_status, username = st.session_state.authenticator.login()
        
        if authentication_status == False:
            st.error('Username/password is incorrect')
            return False
        elif authentication_status == None:
            st.warning('Please enter your username and password')
            return False
        elif authentication_status:
            st.session_state.authentication_status = True
            st.session_state.username = username
            st.session_state.name = name
            
            # Get user info and set session data
            user_info = st.session_state.authenticator.get_user_info(username)
            if user_info:
                st.session_state.user_email = user_info['email']
                st.session_state.user_role = user_info['role']
                st.session_state.company_id = user_info['company_id']
            
            st.rerun()
    
    return True

def get_current_user() -> Optional[dict]:
    """Get current user information from session."""
    if st.session_state.get('authentication_status') == True:
        return {
            'username': st.session_state.get('username'),
            'name': st.session_state.get('name'),
            'email': st.session_state.get('user_email'),
            'role': st.session_state.get('user_role'),
            'company_id': st.session_state.get('company_id')
        }
    return None

def get_current_company_id() -> Optional[int]:
    """Get current company ID from session."""
    return st.session_state.get('company_id')

def is_admin() -> bool:
    """Check if current user is admin."""
    user = get_current_user()
    return user and user.get('role') == 'admin'

def logout():
    """Logout current user."""
    if 'authenticator' in st.session_state:
        st.session_state.authenticator.logout()
    
    # Clear session state
    for key in ['authentication_status', 'username', 'name', 'user_email', 'user_role', 'company_id']:
        if key in st.session_state:
            del st.session_state[key]
    
    st.rerun()

def setup_sidebar():
    """Setup authentication sidebar."""
    user = get_current_user()
    
    if user:
        st.sidebar.write(f"👋 Welcome, {user['name']}")
        st.sidebar.write(f"📧 {user['email']}")
        st.sidebar.write(f"🏢 Company ID: {user['company_id']}")
        st.sidebar.write(f"👤 Role: {user['role'].title()}")
        
        if st.sidebar.button("🚪 Logout"):
            logout()
    else:
        st.sidebar.write("Please login to continue")