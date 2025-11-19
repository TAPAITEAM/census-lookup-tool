#!/usr/bin/env python3
"""
Quick setup check for Census Demographics Lookup Tool
Run this to verify your environment is ready
"""

import sys
import os

print("=" * 60)
print("Census Demographics Lookup - Environment Check")
print("=" * 60)
print()

all_good = True

# Check Python version
print("✓ Checking Python version...")
if sys.version_info >= (3, 7):
    print(f"  ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (OK)")
else:
    print(f"  ❌ Python {sys.version_info.major}.{sys.version_info.minor} (Need 3.7+)")
    all_good = False

print()

# Check required packages
print("✓ Checking required packages...")
required_packages = [
    'streamlit',
    'requests',
    'gspread',
    'oauth2client',
    'pandas',
    'openpyxl'
]

for package in required_packages:
    try:
        __import__(package)
        print(f"  ✅ {package}")
    except ImportError:
        print(f"  ❌ {package} (missing)")
        all_good = False

print()

# Check required files
print("✓ Checking required files...")
required_files = [
    'main_app.py',
    'census_demographics_lookup.py',
    'service_account.json',
    'data/CensusTractList2025_0.xlsx'
]

for file in required_files:
    if os.path.exists(file):
        print(f"  ✅ {file}")
    else:
        print(f"  ⚠️  {file} (missing)")
        if file == 'service_account.json':
            print("     → Google Sheets processing will not work")
        elif file.endswith('.xlsx'):
            print("     → FFIEC income levels will not be available")
        if file != 'data/CensusTractList2025_0.xlsx':  # FFIEC file is optional
            all_good = False

print()
print("=" * 60)

if all_good:
    print("✅ All checks passed! You're ready to run the application.")
    print()
    print("To start the app:")
    print("  • Windows: Double-click START_HERE.bat")
    print("  • Mac/Linux: Double-click START_HERE.sh")
    print("  • Or run: streamlit run main_app.py")
else:
    print("❌ Some checks failed. Please fix the issues above.")
    print()
    print("To install missing packages, run:")
    print("  pip install -r census_requirements.txt")

print("=" * 60)
