# 🚀 Deploying to Streamlit Cloud

## Step-by-Step Deployment Guide

### Prerequisites
- GitHub account
- Your code in a GitHub repository
- Google service account credentials (service_account.json)

---

## 1️⃣ Prepare Your Repository

### Push Code to GitHub

```bash
cd /workspaces/codespaces-jupyter/LMIUpdate

# Initialize git (if not already done)
git init

# Add all files (sensitive files are excluded by .gitignore)
git add .

# Commit
git commit -m "Initial commit - Census Demographics Lookup Tool"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git push -u origin main
```

**⚠️ IMPORTANT:** The `.gitignore` file ensures `service_account.json` is NOT pushed to GitHub.

---

## 2️⃣ Deploy to Streamlit Cloud

### A. Sign Up / Sign In
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "Sign in with GitHub"
3. Authorize Streamlit to access your repositories

### B. Create New App
1. Click **"New app"** button
2. Fill in the deployment form:
   - **Repository:** Select your repo (e.g., `your-username/census-lookup`)
   - **Branch:** `main` (or your default branch)
   - **Main file path:** `LMIUpdate/main_app.py`
   - **App URL:** Choose a custom URL (e.g., `census-lookup`)

3. Click **"Advanced settings"** (optional):
   - Python version: `3.9` or higher
   - Keep other defaults

### C. Configure Secrets
**This is the most important step!**

1. Before clicking "Deploy", click **"Advanced settings"**
2. In the **"Secrets"** section, paste your service account JSON:

```toml
[service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYour-Private-Key-Here\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "your-cert-url"
```

**To get this content:**
- Open your local `service_account.json` file
- Copy the entire JSON content
- Convert it to TOML format for Streamlit secrets

**Quick conversion:**
```python
import json

# Read your service_account.json
with open('service_account.json', 'r') as f:
    data = json.load(f)

# Print in TOML format
print("[service_account]")
for key, value in data.items():
    if isinstance(value, str):
        # Escape quotes and newlines in strings
        value = value.replace('"', '\\"').replace('\n', '\\n')
        print(f'{key} = "{value}"')
    else:
        print(f'{key} = "{value}"')
```

### D. Deploy!
1. Click **"Deploy!"**
2. Wait 2-5 minutes for deployment
3. Your app will be live at: `https://your-app-name.streamlit.app`

---

## 3️⃣ Post-Deployment

### Share the URL
Your app is now accessible at:
```
https://your-app-name.streamlit.app
```

Share this URL with non-technical users - they can bookmark it and use it anytime!

### Update the App
When you push changes to GitHub:
```bash
git add .
git commit -m "Update feature"
git push
```

Streamlit Cloud will automatically redeploy your app!

---

## 4️⃣ Manage Your App

### Access App Dashboard
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click on your app
3. You can:
   - View logs
   - Restart the app
   - Update secrets
   - Delete the app
   - View analytics

### Update Secrets
1. Click on your app in the dashboard
2. Click **"Settings"** → **"Secrets"**
3. Edit the TOML content
4. Click **"Save"**
5. App will restart automatically

### View Logs
If something goes wrong:
1. Click on your app
2. Click **"Manage app"** → **"Logs"**
3. Check for error messages

---

## 5️⃣ Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "No module named 'X'" | Check `requirements.txt` has all dependencies |
| "Secrets not found" | Verify secrets are configured in TOML format |
| "File not found: data/..." | Ensure data files are committed to repo |
| App won't start | Check logs in Streamlit Cloud dashboard |
| "Permission denied" on Google Sheets | Share sheet with service account email |

### Test Locally First
Before deploying, test with Streamlit secrets locally:

1. Create `.streamlit/secrets.toml` (not committed)
2. Add your service account config
3. Run: `streamlit run main_app.py`
4. Verify it works

---

## 6️⃣ Managing the FFIEC Data File

The `data/CensusTractList2025_0.xlsx` file is ~5MB. Options:

### Option A: Include in Repository (Recommended)
- Commit the file to GitHub
- Streamlit Cloud will use it
- Pro: Always available
- Con: Increases repo size

### Option B: Load from External URL
Modify the code to download from a URL:
```python
import requests

def download_ffiec_data():
    url = "YOUR_FILE_URL"
    response = requests.get(url)
    with open('data/CensusTractList2025_0.xlsx', 'wb') as f:
        f.write(response.content)
```

---

## 📊 Your Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] `.gitignore` excludes sensitive files
- [ ] `requirements.txt` exists in LMIUpdate folder
- [ ] Signed in to Streamlit Cloud
- [ ] Created new app with correct repo/branch/path
- [ ] Configured secrets in TOML format
- [ ] Clicked "Deploy"
- [ ] Tested the deployed app URL
- [ ] Shared URL with users

---

## 🎉 Success!

Your app is now live and accessible to anyone with the URL. No installation needed for users!

**Next Steps:**
- Test all features in the deployed app
- Share the URL with your team
- Monitor usage via Streamlit dashboard
- Push updates as needed (auto-deploys)

---

**Estimated Time:** 15-20 minutes for first deployment

**Cost:** FREE (Streamlit Community Cloud is free for public apps)
