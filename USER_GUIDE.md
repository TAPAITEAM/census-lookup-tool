# Census Demographics Lookup - User Guide

## Quick Start (For Non-Technical Users)

### Step 1: Install Required Software (One-Time Setup)

1. **Install Python** (if not already installed):
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Verify: Open Command Prompt/Terminal and type `python --version`

2. **Install Required Packages**:
   - Open Command Prompt (Windows) or Terminal (Mac/Linux)
   - Navigate to this folder
   - Run: `pip install -r census_requirements.txt`

### Step 2: Setup Google Sheets Access (One-Time Setup)

1. Make sure `service_account.json` file is in this folder
2. Ensure the Google Sheet is shared with the email in `service_account.json`

### Step 3: Run the Application

#### **Windows Users:**
- Double-click `START_HERE.bat`
- The application will open in your web browser

#### **Mac/Linux Users:**
- Double-click `START_HERE.sh` (or run `bash START_HERE.sh` in Terminal)
- The application will open in your web browser

### Step 4: Use the Application

#### **Option A: Look Up Single Address**
1. Enter address details in the form:
   - Address (e.g., "25 Drake Ave")
   - City (e.g., "New Rochelle")
   - State (e.g., "New York")
   - ZIP Code (optional)
2. Click "Lookup"
3. View the results showing income level and demographics

#### **Option B: Process Google Sheet**
1. Copy your Google Sheet URL
2. Paste it in the "Google Sheet URL" field
3. Check "Dry run" box to preview results without writing to the sheet
4. Click "Process Google Sheet"
5. Review the results
6. Uncheck "Dry run" and click again to write results to Column C

## Troubleshooting

### "streamlit: command not found"
- Run: `pip install streamlit` or `pip install -r census_requirements.txt`

### "Permission denied" on Mac/Linux
- Run: `chmod +x START_HERE.sh`
- Then try double-clicking again

### Application doesn't open in browser
- Manually open your browser and go to: `http://localhost:8501`

### Google Sheet access denied
- Verify `service_account.json` is in the folder
- Check that the Google Sheet is shared with the email in the service account file
- The email looks like: `lmiupdate@lmiupdate.iam.gserviceaccount.com`

## Expected Google Sheet Format

Your Google Sheet should have:
- **Column A**: Account ID (optional)
- **Column B**: Full Address (e.g., "25 Drake Ave New Rochelle, New York 10805 United States")
- **Column C**: Will be filled with FFIEC Income Level (Low/Middle/Upper)

The address can be in any column with a header containing "address" (case-insensitive).

## Output Income Levels

The tool returns official FFIEC income classifications:
- **Low**: Below-median income tract
- **Middle**: At or near median income tract
- **Upper**: Above-median income tract

These are based on comparing the Census tract's median income to the metropolitan area's median income.

## Support

For technical issues or questions:
1. Check that all required files are present (service_account.json, data/CensusTractList2025_0.xlsx)
2. Verify Python version is 3.7 or higher
3. Ensure all packages are installed correctly

---

**Last Updated:** November 19, 2025
