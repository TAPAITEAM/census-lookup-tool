# Census Demographics Lookup Tool

A standalone Python tool to look up U.S. Census demographic data for any address, including tract-level income information.

## Project Structure

```
Project/
├── Address Inputs/                    # Input address files
│   ├── address_input.csv              # Main address data file
│   └── test_addresses.csv             # Sample address data
├── Results/                           # Output CSV files
│   └── census_results_*.csv           # Generated results with timestamps
├── census_demographics_lookup.py      # Main lookup script
├── census_demographics_prompt.md      # Documentation
├── census_requirements.txt             # Python dependencies
├── data/
│   └── CensusTractList2025_0.xlsx      # FFIEC tract income reference (downloaded)
└── CENSUS_README.md                   # This file
```

## Features

- **Address Geocoding**: Convert addresses to Census tract information
- **Income Classification**: Categorize areas by income level (Very Low to High Income)
- **Demographic Data**: Population, housing, and transportation statistics
- **Caching**: In-memory caching to reduce API calls
- **Multiple Interfaces**: Command-line and interactive modes
- **Batch Processing**: Process multiple addresses from CSV files
- **Fuzzy Address Matching**: Automatically tries multiple address variations
- **Google Maps Integration**: Enabled by default for enhanced geocoding and fallback
- **FFIEC Tract Income Levels**: Adds the official FFIEC classification for each tract using a locally cached reference file
- **CSV Output**: Save results to CSV files in Results folder with full demographic data

## Installation

```bash
pip install -r census_requirements.txt
```

### FFIEC Tract List

Download the latest FFIEC Census Tract List (Excel) and place it in the `data/` directory. The project currently expects `data/CensusTractList2025_0.xlsx` (sheet `2024-2025 tracts`). The first lookup will load the file and cache ~85k tract → income mappings in memory.

## Usage

### Interactive Mode
```bash
python census_demographics_lookup.py
```

### Command Line Mode
```bash
python census_demographics_lookup.py "123 Main St" "New York" "NY" --zip "10001"
```

### Enhanced Geocoding Options
```bash
# Google Maps API is enabled by default for better address matching
python census_demographics_lookup.py "123 Main St" "New York" "NY"

# Use custom Google Maps API key (optional)
python census_demographics_lookup.py "123 Main St" "New York" "NY" --google-api-key "YOUR_API_KEY"

# Disable fuzzy matching for exact matches only
python census_demographics_lookup.py "123 Main St" "New York" "NY" --no-fuzzy
```

### JSON Output
```bash
python census_demographics_lookup.py "123 Main St" "New York" "NY" --json
```

### Batch Processing from Address Inputs
The tool can process addresses from CSV files in the `Address Inputs/` folder:

```bash
# Process addresses from Address Inputs/address_input.csv
python census_demographics_lookup.py --batch "Address Inputs/address_input.csv"

# Save results to CSV file in Results folder
python census_demographics_lookup.py --batch "Address Inputs/address_input.csv" --output-csv

# Save results to custom CSV filename
python census_demographics_lookup.py --batch "Address Inputs/address_input.csv" --output-csv "Results/my_results.csv"
```

**CSV Format**: Each row can contain multiple addresses separated by commas:
```
"781 Old Sleepy Hollow Road ext., Briarcliff Manor NY 10510","555 Washington Ave., Brooklyn NY 11238"
```

**Processing**: The system processes each address individually and shows results by row and column position.

**CSV Output**: Results are saved to the `Results/` folder with simplified columns for easy integration:
- `original_address`: The input address as provided
- `income_level`: ACS-based income classification (Very Low Income, Low Income, Moderate Income, Middle Income, Upper Middle Income, High Income, Data Not Available, or Failed - [error message])
- `ffiec_income_level`: Official FFIEC tract income level (Low, Moderate, Middle, Upper) or an error explanation if the tract was not found

**Example CSV Output**:
```csv
original_address,income_level,ffiec_income_level
"781 Old Sleepy Hollow Road ext., Briarcliff Manor NY 10510",High Income,Upper
"555 Washington Ave., Brooklyn NY 11238",Upper Middle Income,Upper
```

## Google Sheet Integration

You can process addresses directly from a Google Sheet using the Streamlit app:

1. **Sheet Format:**
    - **Column A:** Identifier (e.g., unique ID or name)
    - **Column B:** Address (format: `Street, City State ZIP`)
    - **Column C:** Output (income information will be written here)
2. **Authentication:**
    - Ensure your `service_account.json` is present in the `LMIUpdate/` folder and has access to the target Google Sheet.
3. **Usage:**
    - Run the Streamlit app:
      ```bash
      streamlit run LMIUpdate/app.py
      ```
    - Select **Google Sheet** in the app UI and click **Process Google Sheet**.
    - The app will read identifiers and addresses from columns A and B, look up income information, and write results to column C.

**Note:** The Google Sheet name and worksheet are currently set to `'LMIAddress'` and `'BulkInputSubset'` in the code. You can change these in `app.py` if needed.

## Example Output

```
🏠 Census Demographics Lookup
==================================================
Address: 123 Main St
City: New York
State: NY
ZIP: 10001

🔍 Geocoding address: 123 Main St, New York, NY 10001
📊 Fetching Census data for tract 000100

✅ Address Found!
📍 Standardized: 123 Main St, New York, NY 10001
🗺️  Coordinates: 40.7505, -73.9934

📊 Census Tract Information:
   Tract ID: 36061000100
   State FIPS: 36
   County FIPS: 061
   Tract FIPS: 000100

💰 Income Demographics:
   Median Household Income: $85,000
   Income Level: Upper Middle Income

👥 Population & Housing:
   Total Population: 4,500
   Total Housing Units: 2,200
   Owner Occupied Rate: 35.0%
   Public Transit Commuters: 1,200

📋 Data Source: American Community Survey 5-Year Estimates (2022)
```

## Income Level Classifications

- **Very Low Income**: < $30,000
- **Low Income**: $30,000 - $50,000
- **Moderate Income**: $50,000 - $75,000
- **Middle Income**: $75,000 - $100,000
- **Upper Middle Income**: $100,000 - $150,000
- **High Income**: > $150,000

## Data Sources

- **Geocoding**: U.S. Census Geocoding API
- **Demographics**: American Community Survey (ACS) 5-Year Estimates 2022
- **Income Data**: ACS Table B19013 (Median Household Income)

## API Endpoints Used

- Geocoding: `https://geocoding.geo.census.gov/geocoder/locations/onelineaddress`
- ACS Data: `https://api.census.gov/data/2022/acs/acs5`

## Error Handling

The tool handles common issues:
- Invalid addresses
- API rate limits
- Missing Census data
- Network connectivity issues

## Use Cases

- **Grant Applications**: Demonstrate service to low-income areas
- **Impact Assessment**: Measure service to underserved communities
- **Resource Allocation**: Target resources based on need
- **Reporting**: Generate demographic reports for stakeholders
- **Batch Analysis**: Process multiple addresses from `Address Inputs/` folder for comprehensive demographic studies

## Fuzzy Address Matching

The system automatically tries multiple address variations to improve matching success:

### **Automatic Variations**
1. **Original address** as provided
2. **Normalized abbreviations** (St → Street, Ave → Avenue, etc.)
3. **Cleaned addresses** (removes apartment/unit numbers)
4. **Simplified format** (removes extra punctuation and spaces)

### **Example Variations**
For input: `"123 Main St Apt 2B, New York, NY 10001"`
The system tries:
- `"123 Main St Apt 2B, New York, NY 10001"`
- `"123 Main Street Apt 2B, New York, NY 10001"`
- `"123 Main St, New York, NY 10001"`
- `"123 Main Street, New York, NY 10001"`

### **Google Maps Fallback**
If Census geocoding fails, the system automatically uses Google Maps API:
- ✅ **Enabled by default** with included API key
- Better handling of misspelled addresses
- More comprehensive address database
- Provides standardized address formatting
- Free tier provides thousands of requests per month

## Data & API Requirements

- **FFIEC Tract List**: Download once and place in `data/` (see Installation). Provides official tract income levels.
- **Geocoding API**: https://geocoding.geo.census.gov/geocoder/locations/onelineaddress (free, no key required)
- **ACS Data API**: https://api.census.gov/data/2022/acs/acs5 (free, no key required)
- **Google Maps API**: Optional fallback. The script includes a default key but you should supply your own via `--google-api-key` for production use.

## Limitations

- Requires internet connection
- ACS data has margins of error (especially for small tracts)
- Some tracts may have suppressed data for privacy
- Rate limits apply to Census APIs (but no authentication needed)

## Technical Details

- **Language**: Python 3.8+
- **Dependencies**: `requests`, `pandas`, `openpyxl`
- **Local Data**: FFIEC tract list cached at runtime (Excel file in `data/`)
- **Caching**: In-memory cache to reduce repeated API calls and tract lookups
- **Timeout**: 10-second timeout for API calls
- **Error Recovery**: Graceful handling of API failures

## License

This tool is provided as-is for educational and research purposes. Please respect Census API terms of service.