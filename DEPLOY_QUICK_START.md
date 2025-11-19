# 🚀 Streamlit Cloud Deployment - Quick Start

## What You'll Get
A permanent URL like `https://census-lookup.streamlit.app` that non-technical users can access directly in their browser. No installation required!

---

## ⚡ Fast Track (15 minutes)

### Step 1: Convert Secrets (2 min)
```bash
cd /workspaces/codespaces-jupyter/LMIUpdate
python convert_to_streamlit_secrets.py
```
Copy the output - you'll need it in Step 4.

### Step 2: Push to GitHub (3 min)
```bash
# If not already a git repo
git init
git add .
git commit -m "Census Demographics Lookup Tool"

# Create a new repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 3: Deploy on Streamlit (5 min)
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select:
   - **Repository:** your-username/your-repo
   - **Branch:** main
   - **Main file:** `LMIUpdate/main_app.py`
5. Click **"Advanced settings"**

### Step 4: Add Secrets (3 min)
In the "Secrets" section, paste the output from Step 1 (the TOML format)

### Step 5: Deploy! (2 min)
Click **"Deploy"** - wait 2-5 minutes for build to complete.

---

## 🎉 Done!

Your app is live at: `https://your-app.streamlit.app`

Share this URL with anyone - they can use it immediately!

---

## 📝 Important Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Tells Streamlit Cloud what packages to install |
| `.gitignore` | Prevents sensitive files from being pushed to GitHub |
| `.streamlit/config.toml` | App configuration |
| `convert_to_streamlit_secrets.py` | Helper to convert credentials |

---

## 🔄 Making Updates

After deployment, any changes you push to GitHub will auto-deploy:

```bash
# Make your changes, then:
git add .
git commit -m "Updated feature"
git push
```

Streamlit Cloud automatically redeploys within 1-2 minutes!

---

## 🆘 Troubleshooting

**App won't start?**
- Check logs in Streamlit Cloud dashboard
- Verify secrets are in correct TOML format
- Ensure `requirements.txt` exists

**"Module not found" error?**
- Add missing package to `requirements.txt`
- Push changes to GitHub

**Google Sheets not working?**
- Check secrets are configured
- Verify service account email has access to sheet

---

## 📚 Full Documentation

For detailed instructions, see: [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)

---

**Questions?** Check the logs in your Streamlit Cloud dashboard for detailed error messages.
