# 🏠 Census Demographics Lookup Tool

**Simple tool to look up Census income levels for addresses**

## 🌐 For Non-Technical Users

**Use the deployed web app (no installation needed):**

👉 **[Open the App](https://your-app.streamlit.app)** _(Update this link after deployment)_

Just click the link above - no software to install!

---

## 💻 For Local Installation (3 Steps)

### 1️⃣ First Time Setup

Open Command Prompt (Windows) or Terminal (Mac/Linux) and run:

```bash
pip install -r census_requirements.txt
```

### 2️⃣ Check Everything is Ready

Run the setup checker:

```bash
python check_setup.py
```

If you see ✅ for all checks, you're ready!

### 3️⃣ Start the Application

#### Windows:
Double-click **`START_HERE.bat`**

#### Mac/Linux:
Double-click **`START_HERE.sh`**

The application will open in your web browser!

---

## 📖 What This Tool Does

- **Look up single addresses**: Get Census demographics and FFIEC income level for any US address
- **Process Google Sheets**: Automatically process hundreds of addresses from a spreadsheet
- **Official data**: Uses US Census Bureau data and FFIEC income classifications

---

## 💡 Need Help?

**Read the detailed guide:** [USER_GUIDE.md](USER_GUIDE.md)

**Common Issues:**

| Problem | Solution |
|---------|----------|
| "streamlit: command not found" | Run: `pip install streamlit` |
| "Permission denied" (Mac/Linux) | Run: `chmod +x START_HERE.sh` |
| Google Sheet access denied | Share your sheet with the email in `service_account.json` |
| App doesn't open in browser | Manually go to `http://localhost:8501` |

---

## 📁 File Structure

```
LMIUpdate/
├── START_HERE.bat           ← Double-click this (Windows)
├── START_HERE.sh            ← Double-click this (Mac/Linux)
├── check_setup.py           ← Run this to check if everything is installed
├── USER_GUIDE.md            ← Detailed instructions
├── main_app.py              ← Main application (don't need to edit)
├── census_demographics_lookup.py ← Core logic (don't need to edit)
├── service_account.json     ← Google credentials (required for Sheets)
└── data/
    └── CensusTractList2025_0.xlsx ← FFIEC income data
```

---

## 🎯 Using the Application

### Option A: Single Address
1. Enter address details in the form
2. Click "Lookup"
3. View income level and demographics

### Option B: Batch Process Google Sheet
1. Share your Google Sheet with: `lmiupdate@lmiupdate.iam.gserviceaccount.com`
2. Paste the Google Sheet URL
3. Check "Dry run" to preview first
4. Click "Process Google Sheet"
5. Uncheck "Dry run" and click again to write results

**Your sheet format:**
- Column B: Full address (e.g., "25 Drake Ave New Rochelle, NY 10805")
- Column C: Will be filled with income level (Low/Middle/Upper)

---

## 📊 Income Level Meanings

| Level | Meaning |
|-------|---------|
| **Low** | Below-median income tract |
| **Middle** | At or near median income tract |
| **Upper** | Above-median income tract |

These levels are official FFIEC classifications based on comparing the Census tract's median household income to the metropolitan area's median income.

---

## ⚙️ Technical Details

- **Language:** Python 3.7+
- **Framework:** Streamlit
- **Data Sources:** US Census Bureau Geocoding API, American Community Survey, FFIEC Census Tract List
- **Authentication:** Google Service Account for Sheets API

For technical documentation, see [CENSUS_README.md](CENSUS_README.md)

---

**Last Updated:** November 19, 2025
