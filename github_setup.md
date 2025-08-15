# GitHub Setup Instructions

## 1. Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `cashflow-saas`
3. Description: `Complete Cash Flow Analytics SaaS for SMEs - Built with Streamlit`
4. Set to **Public** (required for free Streamlit Cloud)
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

## 2. Connect Local Repository to GitHub
Replace `YOUR_USERNAME` with your actual GitHub username:

```bash
cd "cashflow-saas"
git remote add origin https://github.com/YOUR_USERNAME/cashflow-saas.git
git branch -M main
git push -u origin main
```

## 3. Deploy to Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Click "New app"
3. Connect your GitHub account if not already connected
4. Select your repository: `YOUR_USERNAME/cashflow-saas`
5. Branch: `main`
6. Main file path: `app.py`
7. Click "Deploy!"

## 4. First Time Setup (Automatic)
- The app will auto-initialize the database with sample data
- Login with: admin/admin123 or analyst/analyst123
- Explore all features!

## 5. Optional: Custom Domain
In Streamlit Cloud settings, you can configure a custom domain like:
`your-company-cashflow.streamlit.app`

## 6. Production Enhancements (Future)
For production SaaS deployment:
- Migrate to PostgreSQL (update DATABASE_URL in secrets)
- Add Stripe billing integration
- Implement OAuth authentication
- Set up custom domain and SSL