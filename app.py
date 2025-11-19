import streamlit as st
import pandas as pd
from  census_demographics_lookup import CensusDemographicsLookup
import gspread
from gspread_dataframe import get_as_dataframe

# Authenticate and open Google Sheet
gc = gspread.service_account(filename='service_account.json')
sh = gc.open('LMIAddress')
worksheet = sh.worksheet('BulkInputSubset')

lookup = CensusDemographicsLookup()
st.title("Census Lookup Demo")

option = st.radio("Choose action", ["Single Lookup", "CSV File", "Google Sheet"])
if option == "Single Lookup":
    st.text("LOOKUP")
    addr = st.text_input("Address")
    city = st.text_input("City")
    state = st.text_input("State")
    zip_code = st.text_input("ZIP Code (optional)")
    if st.button("Submit"):
       result = lookup.lookup_address(addr, city, state, zip_code)
       st.write(result)
elif option == "CSV File":
    st.text("CSV")
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        result_df = lookup.process_csv_dataframe(df)
        st.write(result_df)
elif option == "Google Sheet":
    st.text("Google Sheet")
    if st.button("Process Google Sheet"):
        df = get_as_dataframe(worksheet, evaluate_formulas=True, header=None)
        # Expect columns: A=Identifier, B=Address
        result = lookup.process_google_sheet_dataframe(df)
        # Write FFIEC income level back to worksheet column C
        for idx, res in enumerate(result):
            worksheet.update_cell(idx+1, 3, res.get('ffiec_income_level', res.get('error', 'No result')))
        result_df = pd.DataFrame(result)
        st.write(result_df)