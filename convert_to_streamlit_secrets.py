#!/usr/bin/env python3
"""
Convert service_account.json to Streamlit secrets TOML format
This makes it easy to copy/paste into Streamlit Cloud secrets
"""

import json
import os

print("=" * 70)
print("Convert service_account.json to Streamlit Secrets TOML Format")
print("=" * 70)
print()

# Check if service_account.json exists
if not os.path.exists("service_account.json"):
    print("❌ Error: service_account.json not found in current directory")
    print()
    print("Please ensure service_account.json is in the same folder as this script.")
    exit(1)

try:
    # Read the JSON file
    with open('service_account.json', 'r') as f:
        data = json.load(f)
    
    print("✅ Successfully read service_account.json")
    print()
    print("=" * 70)
    print("COPY THE CONTENT BELOW TO STREAMLIT CLOUD SECRETS:")
    print("=" * 70)
    print()
    print("[service_account]")
    
    # Convert to TOML format
    for key, value in data.items():
        if isinstance(value, str):
            # Escape backslashes first, then quotes
            value = value.replace('\\', '\\\\').replace('"', '\\"')
            # Replace actual newlines with \n
            value = value.replace('\n', '\\n')
            print(f'{key} = "{value}"')
        elif isinstance(value, bool):
            print(f'{key} = {str(value).lower()}')
        elif isinstance(value, (int, float)):
            print(f'{key} = {value}')
        else:
            print(f'{key} = "{value}"')
    
    print()
    print("=" * 70)
    print()
    print("📋 Instructions:")
    print("1. Copy everything between the === lines above")
    print("2. Go to your Streamlit Cloud app settings")
    print("3. Click 'Secrets' in the sidebar")
    print("4. Paste the content")
    print("5. Click 'Save'")
    print()
    print("=" * 70)

except json.JSONDecodeError as e:
    print(f"❌ Error: Invalid JSON in service_account.json")
    print(f"   {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
