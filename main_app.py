import streamlit as st
from census_demographics_lookup import CensusDemographicsLookup
import gspread
from google.oauth2.service_account import Credentials
import os
import json

# Helper function to get Google credentials
def get_google_credentials():
    """Get Google service account credentials from file or Streamlit secrets"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Try Streamlit secrets first (for cloud deployment)
    if "service_account" in st.secrets:
        credentials_dict = dict(st.secrets["service_account"])
        return Credentials.from_service_account_info(credentials_dict, scopes=scopes)
    
    # Fall back to local file (for local development)
    elif os.path.exists("service_account.json"):
        return Credentials.from_service_account_file("service_account.json", scopes=scopes)
    
    else:
        raise FileNotFoundError("No service account credentials found. Add service_account.json or configure Streamlit secrets.")

# Initialize the CensusDemographicsLookup class
lookup = CensusDemographicsLookup()

# Page configuration
st.set_page_config(
    page_title="Census Demographics Lookup",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Census Demographics Lookup Tool")
st.markdown("---")

# Add helpful instructions at the top
with st.expander("ℹ️ How to Use This Tool", expanded=False):
    st.markdown("""
    ### Single Address Lookup
    1. Enter the address, city, and state in the fields below
    2. Click "Lookup" to get Census demographics and FFIEC income level
    
    ### Batch Process Google Sheet
    1. Share your Google Sheet with: `lmiupdate@lmiupdate.iam.gserviceaccount.com`
    2. Your sheet should have addresses in Column B (any header with "address")
    3. Paste the Google Sheet URL below
    4. Check "Dry run" to preview without writing to the sheet
    5. Click "Process Google Sheet"
    6. Results will be written to Column C
    
    ### Expected Income Levels
    - **Low**: Below-median income tract
    - **Middle**: At or near median income tract  
    - **Upper**: Above-median income tract
    """)

# Check if credentials are available
try:
    credentials_available = "service_account" in st.secrets or os.path.exists("service_account.json")
except FileNotFoundError:
    credentials_available = os.path.exists("service_account.json")

if not credentials_available:
    st.warning("⚠️ Google Sheets credentials not configured. Single address lookup will work, but batch processing is disabled.")

st.markdown("## 📍 Single Address Lookup")

# Input fields for address
col1, col2 = st.columns(2)
with col1:
    address = st.text_input("Street Address", placeholder="e.g., 25 Drake Ave")
    state = st.text_input("State", placeholder="e.g., New York or NY")
with col2:
    city = st.text_input("City", placeholder="e.g., New Rochelle")
    zip_code = st.text_input("ZIP Code (optional)", placeholder="e.g., 10805")

# Button to trigger the lookup
if st.button("🔍 Lookup", type="primary"):
    if address and city and state:
        with st.spinner("Looking up address..."):
            result = lookup.lookup_address(address, city, state, zip_code)
        
        if 'error' in result:
            st.error(f"❌ Error: {result.get('message', result['error'])}")
        else:
            st.success("✅ Address found!")
            
            # Display income level prominently
            income_level = result.get('ffiec_income_level', 'N/A')
            st.metric("FFIEC Income Level", income_level)
            
            # Show detailed results in expandable section
            with st.expander("View Detailed Results", expanded=True):
                st.json(result)
    else:
        st.error("❌ Please fill in all required fields (Address, City, State).")

st.markdown("---")
st.markdown("## 📊 Batch Process Google Sheet")

# Option to upload a CSV file
uploaded_file = st.file_uploader("Upload a CSV file with addresses", type=["csv"])
if uploaded_file:
    # Save the uploaded file temporarily
    with open("uploaded_file.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Process the file
    results = lookup.process_csv_file("uploaded_file.csv")
    st.write("Batch Results:")
    st.json(results)

# Function to process Google Sheets
def process_google_sheet(sheet_url):
    # Authenticate using credentials
    credentials = get_google_credentials()
    client = gspread.authorize(credentials)

    # Open the Google Sheet and select the 'BulkInputSubset' worksheet
    sheet = client.open_by_url(sheet_url).worksheet('BulkInputSubset')

    # Fetch all data from the sheet
    data = sheet.get_all_records()
    return data

def process_and_update_google_sheet(sheet_url, dry_run: bool = False):
    # Authenticate using credentials
    credentials = get_google_credentials()
    client = gspread.authorize(credentials)
    # st.write("******Sheet open :")
    sheet = client.open_by_url(sheet_url).worksheet('BulkInputSubset')
    # st.write("******Records :")

    data = sheet.get_all_records()

    # Initialize the lookup class
    lookup = CensusDemographicsLookup()
    results = []
    successes = 0
    failures = 0
    for i, row in enumerate(data, start=2):  # start=2 for row numbers (skip header)
        # Try several possible address header names; some sheets use 'AccountAddress' or other variants
        full_address = (
            row.get("Address") or
            row.get("address") or
            row.get("Full Address") or
            row.get("full_address") or
            row.get("AccountAddress") or
            row.get("accountaddress")
        )
        # Also try any key that contains 'address' (case-insensitive)
        if not full_address:
            for k in row.keys():
                if 'address' in str(k).lower():
                    full_address = row.get(k)
                    break
        if full_address:
            # Use the library parser to split a combined address (handles multi-word states)
            parsed = lookup.parse_full_address(full_address)
            # st.write(f"******Parsing full address: {full_address}")
            # st.write(f"******Parser result: {parsed}")

            if not parsed.get('street') or not parsed.get('city') or not parsed.get('state'):
                msg = "Invalid address format"
                if not dry_run:
                    sheet.update_cell(i, 3, msg)
                results.append({"error": msg, "row": i, "parsed": parsed})
                failures += 1
                continue
            street = parsed.get('street')
            city = parsed.get('city')
            state = parsed.get('state')
            zip_code = parsed.get('zip')
            # Streamlit debug logs
            # st.write(f"*****Processing address: {full_address}")
            # st.write(f"******Parsed components - Street: {street}, City: {city}, State: {state}, ZIP: {zip_code}")
            # Normalize the street (use the project's helper which works well)
            normalized_street = lookup.normalize_address(street)
            # st.write(f"******Normalized street: {normalized_street}")

            # Show address variations from the generator (helpful for debugging Census geocoder behavior)
            variations = lookup.generate_address_variations(normalized_street, city, state, zip_code)
            # st.write("******Address variations:")
            # for v in variations:
            #     st.write(f"- {v}")

            # Primary lookup
            result = lookup.lookup_address(normalized_street, city, state, zip_code)

            # Use Google Maps fallback and reverse geocode if Census geocoder failed and a key is available
            if 'error' in result and lookup.google_maps_api_key:
                st.write("⚠️ Primary Census lookup failed; trying Google Maps fallback...")
                google_result = lookup.geocode_with_google_maps(normalized_street, city, state, zip_code)
                st.write(f"Google geocode result: {google_result}")
                if 'error' not in google_result:
                    reverse_result = lookup.reverse_geocode_for_census_tract(google_result)
                    st.write(f"Reverse geocode result: {reverse_result}")
                    if 'census_geography' in reverse_result:
                        cg = reverse_result['census_geography']
                        demographics = lookup.get_census_demographics(cg['state_fips'], cg['county_fips'], cg['tract_fips'])
                        # Merge results so UI displays demographics as well
                        result = {**google_result, **demographics}
            income_level = result.get("ffiec_income_level", "N/A")
            if not dry_run:
                try:
                    sheet.update_cell(i, 3, income_level)  # Column C
                except Exception as e:
                    results.append({"error": str(e), "row": i})
                    failures += 1
                    continue
            successes += 1
            results.append(result)
        else:
            msg = "Missing address info"
            if not dry_run:
                try:
                    sheet.update_cell(i, 3, msg)
                except Exception as e:
                    results.append({"error": str(e), "row": i})
                    failures += 1
                    continue
            results.append({"error": msg, "row": i})
            failures += 1
    # Summary row for UI
    results_summary = {
        'processed_rows': len(data),
        'successes': successes,
        'failures': failures
    }
    return {'summary': results_summary, 'rows': results}

# Add Google Sheets input to the Streamlit app
st.markdown("""
**Instructions:**
1. Make sure your Google Sheet is shared with: `lmiupdate@lmiupdate.iam.gserviceaccount.com`
2. Your sheet should have a worksheet named 'BulkInputSubset'
3. Addresses should be in a column with a header containing "address"
""")

sheet_url = st.text_input("Google Sheet URL", placeholder="https://docs.google.com/spreadsheets/d/...")

col1, col2 = st.columns([1, 3])
with col1:
    dry_run = st.checkbox("Dry run (preview only)", value=True, help="Check this to preview results without writing to the sheet")

if st.button("📊 Process Google Sheet", type="primary"):
    if sheet_url:
        if not credentials_available:
            st.error("❌ Cannot process Google Sheet: credentials not configured. Add service_account.json or configure Streamlit secrets.")
        else:
            try:
                with st.spinner(f"Processing Google Sheet... (Dry run: {dry_run})"):
                    results = process_and_update_google_sheet(sheet_url, dry_run=dry_run)
                
                summary = results.get('summary', {})
                
                # Display summary metrics
                st.markdown("### 📈 Processing Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Rows", summary.get('processed_rows', 0))
                with col2:
                    st.metric("✅ Successes", summary.get('successes', 0))
                with col3:
                    st.metric("❌ Failures", summary.get('failures', 0))
                
                # Success/info message
                if not dry_run:
                    if summary.get('successes', 0) > 0:
                        st.success(f"✅ Successfully wrote {summary.get('successes', 0)} income levels to column C in your Google Sheet.")
                    if summary.get('failures', 0) > 0:
                        st.warning(f"⚠️ {summary.get('failures', 0)} rows had errors.")
                else:
                    st.info("ℹ️ Dry run complete. No changes were written to the sheet. Uncheck 'Dry run' to write results.")
                
                # Show detailed results in expandable section
                with st.expander("View Detailed Results", expanded=False):
                    st.json(results)
                    
            except Exception as e:
                st.error(f"❌ Error processing Google Sheet: {e}")
                st.markdown("""
                **Common issues:**
                - Sheet not shared with service account email
                - Worksheet 'BulkInputSubset' doesn't exist
                - Invalid Google Sheet URL
                - Missing `service_account.json` file
                """)
    else:
        st.error("❌ Please provide a valid Google Sheet URL.")

# Footer
st.markdown("---")
st.markdown("💡 **Tip:** Start with 'Dry run' checked to preview results before writing to your sheet.")