#!/usr/bin/env python3
"""
Census Demographics Lookup System
Standalone tool to get Census tract income data for addresses
"""

import requests
import json
import time
import csv
import os
import re
from datetime import datetime
from typing import Dict, Optional, Tuple, List
import argparse
import sys
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.auth
from googleapiclient.discovery import build

class CensusDemographicsLookup:
    def __init__(self, google_maps_api_key: str = None):
        self.geocoding_url = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
        self.acs_url = "https://api.census.gov/data/2022/acs/acs5"
        self.google_maps_url = "https://maps.googleapis.com/maps/api/geocode/json"
        # Default Google Maps API key (can be overridden)
        self.google_maps_api_key = google_maps_api_key or "AIzaSyDZ0jEaRgDW8LAe3-BbceIe84WeG2qyXxw"
        self.cache = {}  # Simple in-memory cache
        self.ffiec_tract_lookup = None
        self.ffiec_tract_source = None
        
        # Common address abbreviations for fuzzy matching
        self.address_abbreviations = {
            'street': ['st', 'str', 'st.', 'str.'],
            'avenue': ['ave', 'av', 'ave.', 'av.'],
            'boulevard': ['blvd', 'blv', 'blvd.', 'blv.'],
            'road': ['rd', 'rd.'],
            'drive': ['dr', 'dr.'],
            'lane': ['ln', 'ln.'],
            'court': ['ct', 'ct.'],
            'place': ['pl', 'pl.'],
            'circle': ['cir', 'cir.'],
            'north': ['n', 'n.'],
            'south': ['s', 's.'],
            'east': ['e', 'e.'],
            'west': ['w', 'w.'],
            'northeast': ['ne', 'ne.'],
            'northwest': ['nw', 'nw.'],
            'southeast': ['se', 'se.'],
            'southwest': ['sw', 'sw.']
        }
    
    def normalize_address(self, address: str) -> str:
        """
        Normalize address by expanding common abbreviations
        """
        normalized = address.lower().strip()
        
        # Expand abbreviations
        for full_word, abbreviations in self.address_abbreviations.items():
            for abbr in abbreviations:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(abbr) + r'\b'
                normalized = re.sub(pattern, full_word, normalized)
        
        return normalized
    
    def generate_address_variations(self, address: str, city: str, state: str, zip_code: str = None) -> List[str]:
        """
        Generate multiple variations of an address for fuzzy matching
        """
        variations = []
        
        # Original address
        full_address = f"{address}, {city}, {state}"
        if zip_code:
            full_address += f" {zip_code}"
        variations.append(full_address)
        
        # Normalized address
        normalized_address = self.normalize_address(address)
        normalized_full = f"{normalized_address}, {city}, {state}"
        if zip_code:
            normalized_full += f" {zip_code}"
        variations.append(normalized_full)
        
        # Without apartment/unit numbers
        clean_address = re.sub(r'\b(apt|apartment|unit|ste|suite|#)\b.*', '', address, flags=re.IGNORECASE).strip()
        if clean_address != address:
            clean_full = f"{clean_address}, {city}, {state}"
            if zip_code:
                clean_full += f" {zip_code}"
            variations.append(clean_full)
        
        # Remove extra spaces and punctuation
        clean_variation = re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', address)).strip()
        if clean_variation != address:
            clean_full = f"{clean_variation}, {city}, {state}"
            if zip_code:
                clean_full += f" {zip_code}"
            variations.append(clean_full)
        
        return list(set(variations))  # Remove duplicates
    
    def geocode_with_google_maps(self, address: str, city: str, state: str, zip_code: str = None) -> Dict:
        """
        Geocode address using Google Maps API (requires API key)
        """
        if not self.google_maps_api_key:
            return {'error': 'Google Maps API key not provided'}
        
        full_address = f"{address}, {city}, {state}"
        if zip_code:
            full_address += f" {zip_code}"
        
        params = {
            'address': full_address,
            'key': self.google_maps_api_key
        }
        
        try:
            # print(f"🔍 Geocoding with Google Maps: {full_address}")
            response = requests.get(self.google_maps_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'OK' or not data['results']:
                return {
                    'error': 'Address not found in Google Maps',
                    'message': f'Google Maps status: {data.get("status", "Unknown")}'
                }
            
            result = data['results'][0]
            location = result['geometry']['location']
            
            # Extract address components
            address_components = {}
            for component in result['address_components']:
                for component_type in component['types']:
                    address_components[component_type] = component['long_name']
            
            return {
                'address': {
                    'input': full_address,
                    'standardized': result['formatted_address'],
                    'coordinates': {
                        'latitude': location['lat'],
                        'longitude': location['lng']
                    }
                },
                'google_maps_data': {
                    'place_id': result['place_id'],
                    'formatted_address': result['formatted_address'],
                    'address_components': address_components
                }
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'error': 'Google Maps API error',
                'message': str(e)
            }
        except Exception as e:
            return {
                'error': 'Unexpected error with Google Maps',
                'message': str(e)
            }
    
    def reverse_geocode_for_census_tract(self, google_result: Dict) -> Dict:
        """
        Use Census reverse geocoding to get tract data from Google Maps coordinates
        """
        try:
            lat = google_result['address']['coordinates']['latitude']
            lng = google_result['address']['coordinates']['longitude']
            
            # Use Census reverse geocoding API
            reverse_url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
            params = {
                'x': lng,
                'y': lat,
                'benchmark': '2020',
                'format': 'json'
            }
            
            print(f"🔄 Reverse geocoding coordinates: {lat}, {lng}")
            response = requests.get(reverse_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['result']['addressMatches']:
                match = data['result']['addressMatches'][0]
                geographies = match.get('geographies', {})
                census_tracts = geographies.get('Census Tracts', [])
                
                if census_tracts:
                    tract_data = census_tracts[0]
                    
                    # Combine Google Maps data with Census tract data
                    result = {
                        **google_result,
                        'census_geography': {
                            'state_fips': tract_data['STATE'],
                            'county_fips': tract_data['COUNTY'],
                            'tract_fips': tract_data['TRACT'],
                            'tract_id': f"{tract_data['STATE']}{tract_data['COUNTY']}{tract_data['TRACT']}",
                            'block_group': tract_data.get('BLKGRP', '')
                        }
                    }
                    return result
            
            # If reverse geocoding failed, return Google Maps result without Census data
            return {
                **google_result,
                'error': 'Census tract data not available',
                'message': 'Address found via Google Maps but Census tract data unavailable'
            }
            
        except Exception as e:
            return {
                **google_result,
                'error': 'Reverse geocoding failed',
                'message': f'Could not get Census tract data: {str(e)}'
            }
        
    def geocode_address(self, address: str, city: str, state: str, zip_code: str = None, use_fuzzy_matching: bool = True) -> Dict:
        """
        Geocode an address using U.S. Census Geocoding API with fuzzy matching fallback
        """
        # print(f"🔍 Geocode Address Debug: Address: {address}, City: {city}, State: {state}, ZIP: {zip_code}")

        # Debug log for cache check
        cache_key = f"{address}, {city}, {state}, {zip_code}".lower().strip()
        # if cache_key in self.cache:
        #     print(f"Cache hit for key: {cache_key}")
        # else:
        #     print(f"Cache miss for key: {cache_key}")

        # Debug log for address variations
        # if use_fuzzy_matching:
        #     print(f"Using fuzzy matching for address variations.")
        # else:
        #     print(f"Fuzzy matching disabled.")

        # Generate address variations for fuzzy matching
        if use_fuzzy_matching:
            address_variations = self.generate_address_variations(address, city, state, zip_code)
        else:
            address_variations = [f"{address}, {city}, {state}" + (f" {zip_code}" if zip_code else "")]
        
        # Debug log for each variation
        # for i, full_address in enumerate(address_variations):
        #     print(f"Trying variation {i + 1}: {full_address}")

        # Try each variation
        for i, full_address in enumerate(address_variations):
            params = {
                'address': full_address,
                'benchmark': '2020',
                'vintage': '2020',
                'format': 'json'
            }
            
            try:
                # print(f"🔍 Geocoding address variation {i+1}/{len(address_variations)}: {full_address}")
                response = requests.get(self.geocoding_url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if data['result']['addressMatches']:
                    # Success! Extract the first match
                    match = data['result']['addressMatches'][0]
                    coordinates = match['coordinates']
                    
                    # Get Census geography data
                    geographies = match.get('geographies', {})
                    census_tracts = geographies.get('Census Tracts', [])
                    
                    if not census_tracts:
                        continue  # Try next variation
                    
                    tract_data = census_tracts[0]
                    
                    result = {
                        'address': {
                            'input': full_address,
                            'standardized': match.get('matchedAddress', full_address),
                            'coordinates': {
                                'latitude': coordinates['y'],
                                'longitude': coordinates['x']
                            }
                        },
                        'census_geography': {
                            'state_fips': tract_data['STATE'],
                            'county_fips': tract_data['COUNTY'],
                            'tract_fips': tract_data['TRACT'],
                            'tract_id': f"{tract_data['STATE']}{tract_data['COUNTY']}{tract_data['TRACT']}",
                            'block_group': tract_data.get('BLKGRP', '')
                        }
                    }
                    
                    # Cache the result
                    self.cache[cache_key] = result
                    return result
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️  API error for variation {i+1}: {str(e)}")
                continue
            except Exception as e:
                print(f"⚠️  Unexpected error for variation {i+1}: {str(e)}")
                continue
        
        # Debug log for Google Maps fallback
        if self.google_maps_api_key:
            print("🔄 Google Maps fallback enabled.")
        else:
            print("🔄 Google Maps fallback not enabled.")

        # If all variations failed, try Google Maps as fallback (if API key provided)
        if self.google_maps_api_key:
            print("🔄 Trying Google Maps as fallback...")
            google_result = self.geocode_with_google_maps(address, city, state, zip_code)
            if 'error' not in google_result:
                # Try to use Google Maps standardized address with Census API
                standardized_address = google_result['address']['standardized']
                print(f"🔄 Retrying with Google Maps standardized address: {standardized_address}")
                
                # Extract components from Google Maps result
                components = google_result.get('google_maps_data', {}).get('address_components', {})
                
                # Try Census API with the standardized address
                params = {
                    'address': standardized_address,
                    'benchmark': '2020',
                    'vintage': '2020',
                    'format': 'json'
                }
                
                try:
                    response = requests.get(self.geocoding_url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data['result']['addressMatches']:
                        match = data['result']['addressMatches'][0]
                        geographies = match.get('geographies', {})
                        census_tracts = geographies.get('Census Tracts', [])
                        
                        if census_tracts:
                            tract_data = census_tracts[0]
                            
                            result = {
                                'address': {
                                    'input': f"{address}, {city}, {state}" + (f" {zip_code}" if zip_code else ""),
                                    'standardized': match.get('matchedAddress', standardized_address),
                                    'coordinates': google_result['address']['coordinates']
                                },
                                'census_geography': {
                                    'state_fips': tract_data['STATE'],
                                    'county_fips': tract_data['COUNTY'],
                                    'tract_fips': tract_data['TRACT'],
                                    'tract_id': f"{tract_data['STATE']}{tract_data['COUNTY']}{tract_data['TRACT']}",
                                    'block_group': tract_data.get('BLKGRP', '')
                                },
                                'google_maps_enhanced': True
                            }
                            
                            # Cache the result
                            self.cache[cache_key] = result
                            return result
                
                except Exception as e:
                    print(f"⚠️  Census retry failed: {str(e)}")
                
                # If Census retry failed, return Google Maps result without Census data
                return {
                    **google_result,
                    'error': 'Census tract data not available',
                    'message': 'Address found via Google Maps but Census tract data unavailable'
                }
        
        # All attempts failed
        return {
            'error': 'Address not found',
            'message': f'Could not find address after trying {len(address_variations)} variations',
            'tried_variations': address_variations,
            'suggestions': [
                'Check address spelling',
                'Try without apartment/unit numbers',
                'Use ZIP code for better accuracy',
                'Consider using Google Maps API key for better matching'
            ]
        }
    
    def get_census_demographics(self, state_fips: str, county_fips: str, tract_fips: str) -> Dict:
        """
        Get Census demographics for a specific tract
        """
        # Check cache
        cache_key = f"{state_fips}{county_fips}{tract_fips}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # ACS variables to retrieve
        variables = [
            'B19013_001E',  # Median household income
            'B01003_001E',  # Total population
            'B25003_001E',  # Total housing units
            'B25003_002E',  # Owner occupied housing
            'B08301_010E'   # Public transportation commuters
        ]
        
        params = {
            'get': ','.join(variables),
            'for': f'tract:{tract_fips}',
            'in': [f'state:{state_fips}', f'county:{county_fips}']
        }
        
        try:
            print(f"📊 Fetching Census data for tract {tract_fips}")
            response = requests.get(self.acs_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if len(data) < 2:  # Header + data row
                return {
                    'error': 'No Census data available',
                    'message': f'No ACS data found for tract {tract_fips}'
                }
            
            # Extract data (first row is headers, second is data)
            headers = data[0]
            values = data[1]
            
            # Create dictionary mapping
            census_data = dict(zip(headers, values))
            
            # Process the data
            result = {
                'demographics': {
                    'median_household_income': int(census_data.get('B19013_001E', -666666666)) if census_data.get('B19013_001E') not in ['-666666666', '-666666'] else None,
                    'total_population': int(census_data.get('B01003_001E', 0)),
                    'total_housing_units': int(census_data.get('B25003_001E', 0)),
                    'owner_occupied_housing': int(census_data.get('B25003_002E', 0)),
                    'public_transportation_commuters': int(census_data.get('B08301_010E', 0))
                },
                'data_source': {
                    'survey': 'American Community Survey 5-Year Estimates',
                    'year': '2022',
                    'confidence': 'High',
                    'last_updated': '2023-12-14'
                }
            }
            
            # Calculate derived metrics
            if result['demographics']['total_housing_units'] > 0:
                result['demographics']['owner_occupied_rate'] = round(
                    result['demographics']['owner_occupied_housing'] / 
                    result['demographics']['total_housing_units'], 3
                )
            else:
                result['demographics']['owner_occupied_rate'] = None
            
            # Classify income level
            income = result['demographics']['median_household_income']
            if income:
                result['demographics']['income_level'] = self.classify_income_level(income)
            else:
                result['demographics']['income_level'] = 'Data Not Available'
            
            # Cache the result
            self.cache[cache_key] = result
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                'error': 'Census API error',
                'message': str(e)
            }
        except Exception as e:
            return {
                'error': 'Unexpected error',
                'message': str(e)
            }

    def load_ffiec_tract_lookup(self) -> None:
        """Lazy-load FFIEC tract income classifications from local reference file."""
        if self.ffiec_tract_lookup is not None:
            return
    
        reference_path_candidates = [
            os.path.join("data", "CensusTractList2025_0.xlsx"),
            os.path.join("data", "FFIEC_Census_Tract_List.xlsx"),
        ]
    
        reference_path = next((path for path in reference_path_candidates if os.path.exists(path)), None)
    
        if not reference_path:
            print("⚠️  FFIEC tract list not found. Place the Excel file in the data/ directory to enable official income levels.")
            self.ffiec_tract_lookup = {}
            self.ffiec_tract_source = None
            return
    
        try:
            import pandas as pd  # type: ignore
        except ImportError:
            print("⚠️  pandas is required to read the FFIEC tract list. Install with 'pip install pandas openpyxl'.")
            self.ffiec_tract_lookup = {}
            self.ffiec_tract_source = None
            return
    
        try:
            sheet_name_candidates = ["2024-2025 tracts", "2025-2024", 0]
            df = None
            for sheet_name in sheet_name_candidates:
                try:
                    df = pd.read_excel(
                        reference_path,
                        sheet_name=sheet_name,
                        dtype={"FIPS code": str, "Tract income level": str},
                        engine="openpyxl"
                    )
                    break
                except ValueError:
                    continue
    
            if df is None:
                raise ValueError("Could not find expected sheet in FFIEC tract list file")
    
            df = df.dropna(subset=["FIPS code", "Tract income level"])
            df["FIPS code"] = df["FIPS code"].astype(str).str.replace(".0", "", regex=False).str.zfill(11)
            self.ffiec_tract_lookup = dict(zip(df["FIPS code"], df["Tract income level"].str.strip()))
            self.ffiec_tract_source = os.path.basename(reference_path)
            print(f"✅ FFIEC tract income levels loaded from {self.ffiec_tract_source} ({len(self.ffiec_tract_lookup):,} tracts)")
        except Exception as e:
            print(f"⚠️  Could not load FFIEC tract list: {e}")
            self.ffiec_tract_lookup = {}
            self.ffiec_tract_source = None
    
    def get_ffiec_income_level(self, address_data: Optional[Dict], census_geography: Dict) -> Dict:
        """
        Retrieve official FFIEC tract income level classification for the address
        """
        if not census_geography:
            return {'ffiec_income_level': None, 'ffiec_error': 'No census geography available for FFIEC lookup'}

        tract_id = census_geography.get('tract_id')
        if not tract_id:
            state = census_geography.get('state_fips')
            county = census_geography.get('county_fips')
            tract = census_geography.get('tract_fips')
            if state and county and tract:
                tract_id = f"{state}{county}{tract}"

        if not tract_id:
            return {'ffiec_income_level': None, 'ffiec_error': 'Unable to determine tract identifier'}

        cache_key = f"ffiec::{tract_id}"
        if cache_key in self.cache:
            return dict(self.cache[cache_key])

        self.load_ffiec_tract_lookup()

        result: Dict[str, Optional[str]] = {'ffiec_income_level': None}

        if self.ffiec_tract_lookup:
            income_level = self.ffiec_tract_lookup.get(tract_id)
            if income_level:
                result['ffiec_income_level'] = income_level
                # print("******INCOME LEVEL FOUND******")
                result['ffiec_source'] = self.ffiec_tract_source or 'local_file'
            else:
                result['ffiec_error'] = 'Tract not present in FFIEC reference file'
        else:
            result['ffiec_error'] = 'FFIEC reference data unavailable'

        self.cache[cache_key] = dict(result)
        return dict(result)

    def classify_income_level(self, income: int) -> str:
        """Classify income level based on median household income"""
        if income < 30000:
            return "Very Low Income"
        elif income < 50000:
            return "Low Income"
        elif income < 75000:
            return "Moderate Income"
        elif income < 100000:
            return "Middle Income"
        elif income < 150000:
            return "Upper Middle Income"
        else:
            return "High Income"
    
    def lookup_address(self, address: str, city: str, state: str, zip_code: str = None, use_fuzzy_matching: bool = True) -> Dict:
        """
        Complete lookup: address -> demographics
        """
        print(f"\n🏠 Census Demographics Lookup")
        print(f"=" * 50)
        print(f"Address: {address}")
        print(f"City: {city}")
        print(f"State: {state}")
        if zip_code:
            print(f"ZIP: {zip_code}")
        print()
        
        # Step 1: Geocode address
        # print(f"🔍 Geocoding address...")
        geocode_result = self.geocode_address(address, city, state, zip_code, use_fuzzy_matching)
        
        if 'error' in geocode_result:
            return geocode_result
        
        # Step 2: Get Census demographics
        geography = geocode_result['census_geography']
        # print(f"\n🏠 populating result")
        demographics_result = self.get_census_demographics(
            geography['state_fips'],
            geography['county_fips'],
            geography['tract_fips']
        )
        
        if 'error' in demographics_result:
            return {
                **geocode_result,
                'error': demographics_result['error'],
                'message': demographics_result['message']
            }
        
        # Combine results
        # print(f"\n🏠 combining result")
        result = {
            **geocode_result,
            **demographics_result
        }

        # Augment with FFIEC tract income classification when available
        try:
            # print(f"\n🏠 Getting FFIEC TRACT income level...")
            ffiec_result = self.get_ffiec_income_level(result.get('address'), result.get('census_geography', {}))
            # print(result)
            result.update(ffiec_result)
        except Exception as e:
            # Capture unexpected errors without interrupting the lookup flow
            result['ffiec_income_level'] = None
            result['ffiec_error'] = f'Unexpected FFIEC processing error: {e}'
        
        # Debug log to confirm hardcoded logic is triggered
        # if address == "25 Drake Ave" and city == "New Rochelle" and state == "New York" and zip_code == "10805":
        #     print("✅ Hardcoded logic triggered for address: 25 Drake Ave, New Rochelle, New York 10805")

        # Debug log for final result before returning
        # print(f"🔍 Final lookup result: {result}")
        
        return result

    def parse_full_address(self, full_address: str) -> Dict[str, Optional[str]]:
        """
        Try to split a full address string into street, city, state, and zip.

        Returns a dict: { 'street': str, 'city': str, 'state': str, 'zip': str }
        This is a heuristic parser — it handles common US address formats and
        multi-word state names (e.g., "New York"). It looks for zip codes and
        state names/abbreviations to find likely splits.
        """
        if not full_address or not str(full_address).strip():
            return {'street': None, 'city': None, 'state': None, 'zip': None}

        addr = str(full_address).strip()

        # Remove trailing country markers
        addr = addr.replace('United States', '').replace('USA', '').strip()

        # Pre-built list of states (full names and abbreviations)
        STATES = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
            'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
            'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
            'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
            'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
            'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
            'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
            'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
            'DC': 'District of Columbia'
        }

        # Also create a normalized set of full state names
        STATE_NAMES = {v.lower(): k for k, v in STATES.items()}

        # Look for a ZIP code at the end
        import re
        zip_match = re.search(r"(\d{5}(?:-\d{4})?)$", addr)
        zip_code = zip_match.group(1) if zip_match else None
        if zip_code:
            addr = addr[:zip_match.start()].strip(', ').strip()

        # If there is a comma, split on commas; the last comma-separated portion often contains state
        if ',' in addr:
            left, right = addr.rsplit(',', 1)
            left = left.strip()
            right = right.strip()

            # Right might be "State" or "City State" depending on format
            right_tokens = right.split()

            # Try two-word state first
            possible_state = None
            if len(right_tokens) >= 2:
                last_two = ' '.join(right_tokens[-2:]).lower()
                if last_two in STATE_NAMES:
                    possible_state = STATE_NAMES[last_two]
                    city = ' '.join(right_tokens[:-2]).strip() if len(right_tokens) > 2 else None
                    # Heuristic: if city looks too short (1 word) and left ends with two title-case words,
                    # the city may actually be in the left portion of the comma-separated string.
                    if (not city) or (city and len(city.split()) < 2):
                        left_tokens = left.split()
                        if len(left_tokens) >= 2 and left_tokens[-2][0].isupper() and left_tokens[-1][0].isupper():
                            # Move the trailing two words from the left side into city
                            city = ' '.join(left_tokens[-2:]).strip()
                            left = ' '.join(left_tokens[:-2]).strip()
                else:
                    # Try last token alone
                    last_one = right_tokens[-1].lower()
                    if last_one in STATE_NAMES:
                        possible_state = STATE_NAMES[last_one]
                        city = ' '.join(right_tokens[:-1]).strip() if len(right_tokens) > 1 else None
                    else:
                        possible_state = None
                        city = ' '.join(right_tokens).strip() if right_tokens else None

            else:
                last_one = right_tokens[-1].lower()
                if last_one in STATE_NAMES:
                    possible_state = STATE_NAMES[last_one]
                    city = ' '.join(right_tokens[:-1]).strip() if len(right_tokens) > 1 else None
                else:
                    city = right

            # If state not found in right, check left (city might be on the left side)
            if not possible_state:
                # Check if the last token of left is a state name or abbr
                left_tokens = left.split()
                if left_tokens and left_tokens[-1].lower() in STATE_NAMES:
                    possible_state = left_tokens[-1].upper()
                    street = ' '.join(left_tokens[:-1]).strip()
                else:
                    # Try heuristic to discover a trailing city in the left part
                    # Example: "25 Drake Ave New Rochelle" -> street: "25 Drake Ave", city "New Rochelle"
                    if left_tokens and any(ch.isdigit() for ch in left_tokens[0]):
                        # If the left portion contains both street and city, try to split after
                        # the most-likely street suffix (Ave, St, Blvd, Rd, Dr, etc.)
                        street_suffixes = set(['ave', 'avenue', 'st', 'street', 'rd', 'road', 'dr', 'drive', 'blvd', 'boulevard', 'ln', 'lane', 'ct', 'court', 'pl', 'place'])
                        split_idx = None
                        for idx, token in enumerate(left_tokens):
                            if token.lower().rstrip('.') in street_suffixes:
                                split_idx = idx
                        if split_idx is not None and split_idx < len(left_tokens) - 1:
                            # city is the rest after the street suffix
                            city = ' '.join(left_tokens[split_idx+1:]).strip()
                            street = ' '.join(left_tokens[:split_idx+1]).strip()
                        else:
                            # If the last two tokens are title-cased words, assume they're the city
                            if len(left_tokens) >= 2 and (left_tokens[-2][0].isupper() and left_tokens[-1][0].isupper() or left_tokens[-2].lower() in ['new', 'north', 'south', 'east', 'west', 'st', 'saint', 'fort']):
                                city = ' '.join(left_tokens[-2:]).strip()
                                street = ' '.join(left_tokens[:-2]).strip()
                            else:
                                city = left_tokens[-1]
                                street = ' '.join(left_tokens[:-1]).strip()
                    else:
                        street = left

            else:
                street = left

            state = possible_state

            # If city is empty, try finding it from the left side (split by last space)
            if not city:
                # naive split: last word(s) of street look like city when a street number or designator present
                street_parts = street.split()
                if street_parts and any(ch.isdigit() for ch in street_parts[0]):
                    # Assume first words are unit/street, last words are city
                    # This is heuristic and may be imperfect
                    city = street_parts[-1]
                    street = ' '.join(street_parts[:-1]).strip()

        else:
            # No comma: try to split by state and city using tokens
            tokens = addr.split()
            state = None
            city = None
            street = None
            # Try to find a token or adjacent tokens that represent state (lookup STATE_NAMES)
            for i in range(len(tokens)-1, -1, -1):
                # check two-token (multi-word state)
                if i-1 >= 0:
                    two = ' '.join(tokens[i-1:i+1]).lower()
                    if two in STATE_NAMES:
                        state = STATE_NAMES[two]
                        city = tokens[i-2] if i-2 >= 0 else None
                        street = ' '.join(tokens[:i-2]) if i-2 >= 0 else None
                        break

                one = tokens[i].lower()
                if one in STATE_NAMES:
                    state = STATE_NAMES[one]
                    city = tokens[i-1] if i-1 >= 0 else None
                    street = ' '.join(tokens[:i-1]) if i-1 >= 0 else None
                    break

            if not state:
                # fallback: treat last token as zip (already removed) and last two tokens as state+zip may have been missing
                street = ' '.join(tokens[:-2])
                city = tokens[-2] if len(tokens) >= 2 else None

        # Normalize results
        street = street.strip() if street else None
        city = city.strip() if city else None
        state = state.strip() if state else None
        zip_code = zip_code.strip() if zip_code else None

        return {'street': street, 'city': city, 'state': state, 'zip': zip_code}
    
    def print_results(self, result: Dict):
        """Print formatted results"""
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            print(f"   {result['message']}")
            if 'suggestions' in result:
                print("   Suggestions:")
                for suggestion in result['suggestions']:
                    print(f"   - {suggestion}")
            return
        
        print(f"✅ Address Found!")
        print(f"📍 Standardized: {result['address']['standardized']}")
        print(f"🗺️  Coordinates: {result['address']['coordinates']['latitude']:.4f}, {result['address']['coordinates']['longitude']:.4f}")
        print()
        
        print(f"📊 Census Tract Information:")
        print(f"   Tract ID: {result['census_geography']['tract_id']}")
        print(f"   State FIPS: {result['census_geography']['state_fips']}")
        print(f"   County FIPS: {result['census_geography']['county_fips']}")
        print(f"   Tract FIPS: {result['census_geography']['tract_fips']}")
        print()
        
        print(f"💰 Income Demographics:")
        demographics = result['demographics']
        if demographics['median_household_income']:
            print(f"   Median Household Income: ${demographics['median_household_income']:,}")
            print(f"   Income Level: {demographics['income_level']}")
        else:
            print(f"   Income Data: Not Available")

        ffiec_income_level = result.get('ffiec_income_level')
        if ffiec_income_level:
            print(f"   FFIEC Tract Income Level: {ffiec_income_level}")
        elif result.get('ffiec_error'):
            print(f"   FFIEC Tract Income Level: Not Available ({result['ffiec_error']})")
        print()
        
        print(f"👥 Population & Housing:")
        print(f"   Total Population: {demographics['total_population']:,}")
        print(f"   Total Housing Units: {demographics['total_housing_units']:,}")
        if demographics['owner_occupied_rate']:
            print(f"   Owner Occupied Rate: {demographics['owner_occupied_rate']:.1%}")
        print(f"   Public Transit Commuters: {demographics['public_transportation_commuters']:,}")
        print()
        
        print(f"📋 Data Source: {result['data_source']['survey']} ({result['data_source']['year']})")
    
    def process_csv_file(self, csv_file_path: str) -> List[Dict]:
        """
        Process multiple addresses from a CSV file in Address Inputs folder
        """
        if not os.path.exists(csv_file_path):
            return [{'error': 'File not found', 'message': f'CSV file not found: {csv_file_path}'}]
        
        results = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                
                for row_num, row in enumerate(csv_reader, 1):
                    if not row:
                        continue
                    
                    # Process each address in the row (comma-separated)
                    for col_num, address_string in enumerate(row):
                        if not address_string.strip():
                            continue
                        
                        address_string = address_string.strip().strip('"')
                        
                        # Remove country if present
                        if address_string.endswith("United States"):
                            address_string = address_string.replace("United States", "").strip()

                        # Debug log for cleaned address
                        print(f"Cleaned Address: {address_string}")

                        # Parse the address string (format: "Street, City State ZIP")
                        parts = address_string.split(',')
                        if len(parts) < 2:
                            results.append({
                                'row': row_num,
                                'column': col_num + 1,
                                'address': address_string,
                                'error': 'Invalid format',
                                'message': 'Address must be in format: "Street, City State ZIP"'
                            })
                            continue
                        
                        street = parts[0].strip()
                        city_state_zip = parts[1].strip()
                        
                        # Split city, state, zip
                        city_state_parts = city_state_zip.split()
                        if len(city_state_parts) < 2:
                            results.append({
                                'row': row_num,
                                'column': col_num + 1,
                                'address': address_string,
                                'error': 'Invalid format',
                                'message': 'Must include city and state'
                            })
                            continue
                        
                        state = city_state_parts[-2]  # Second to last part
                        zip_code = city_state_parts[-1] if city_state_parts[-1].isdigit() else None
                        city = ' '.join(city_state_parts[:-2]) if zip_code else ' '.join(city_state_parts[:-1])
                        
                        print(f"\n📋 Processing Row {row_num}, Column {col_num + 1}: {address_string}")
                        result = self.lookup_address(street, city, state, zip_code)
                        result['row'] = row_num
                        result['column'] = col_num + 1
                        result['original_address'] = address_string
                        results.append(result)
                        
                        # Add small delay to respect API rate limits
                        time.sleep(0.5)
            
            return results
            
        except Exception as e:
            return [{'error': 'File processing error', 'message': str(e)}]
    
    def print_batch_results(self, results: List[Dict]):
        """Print formatted results for batch processing"""
        print(f"\n📊 Batch Processing Results")
        print(f"=" * 50)
        print(f"Total addresses processed: {len(results)}")
        
        successful = [r for r in results if 'error' not in r]
        failed = [r for r in results if 'error' in r]
        
        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")
        
        if failed:
            print(f"\n❌ Failed Addresses:")
            for result in failed:
                row_info = f"Row {result.get('row', '?')}"
                if 'column' in result:
                    row_info += f", Column {result['column']}"
                print(f"   {row_info}: {result.get('original_address', 'Unknown')}")
                print(f"   Error: {result['error']} - {result['message']}")
        
        if successful:
            print(f"\n✅ Successful Results Summary:")
            income_levels = {}
            for result in successful:
                income_level = result.get('demographics', {}).get('income_level', 'Unknown')
                income_levels[income_level] = income_levels.get(income_level, 0) + 1
            
            for level, count in income_levels.items():
                print(f"   {level}: {count} addresses")

            ffiec_levels = {}
            for result in successful:
                ffiec_level = result.get('ffiec_income_level') or 'FFIEC Not Available'
                ffiec_levels[ffiec_level] = ffiec_levels.get(ffiec_level, 0) + 1

            print(f"\n   FFIEC Tract Income Levels:")
            for level, count in ffiec_levels.items():
                print(f"   - {level}: {count} addresses")
    
    def save_results_to_csv(self, results: List[Dict], output_file: str = None) -> str:
        """
        Save results to CSV file in Results folder
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"Results/census_results_{timestamp}.csv"
        
        # Ensure Results directory exists
        os.makedirs("Results", exist_ok=True)
        
        # Prepare CSV data - simplified for other system integration
        csv_data = []
        for result in results:
            if 'error' in result:
                # Handle failed results
                csv_data.append({
                    'original_address': result.get('original_address', ''),
                    'income_level': 'Failed - ' + result.get('message', result.get('error', 'Unknown error')),
                    'ffiec_income_level': result.get('ffiec_income_level') or result.get('ffiec_error', '')
                })
            else:
                # Handle successful results
                demographics = result.get('demographics', {})
                ffiec_value = result.get('ffiec_income_level')
                if not ffiec_value and result.get('ffiec_error'):
                    ffiec_value = f"Error - {result['ffiec_error']}"
                
                csv_data.append({
                    'original_address': result.get('original_address', ''),
                    'income_level': demographics.get('income_level', 'Data Not Available'),
                    'ffiec_income_level': ffiec_value or ''
                })
        
        # Write CSV file
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'original_address', 'income_level', 'ffiec_income_level'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            
            print(f"\n📁 Results saved to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error saving CSV file: {str(e)}")
            return ""
            
    def _get_google_sheets_service(self):
        """
        Authenticate and create a Google Sheets API service object.
        """
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = None
        
        try:
            # In Google Cloud Shell, this will automatically use the logged-in user's credentials.
            creds, project = google.auth.default(scopes=SCOPES)
            print("✅ Authenticated successfully using Cloud Shell user credentials.")
        except Exception as e:
            print(f"❌ Automatic authentication failed: {e}")
            print("   Please ensure you are logged in to gcloud and have the correct permissions.")
            return None
        
        try:
            service = build('sheets', 'v4', credentials=creds, client_options={'quota_project_id': 'lmiupdate'})
            return service
        except Exception as e:
            print(f"❌ Error building Google Sheets service: {e}")
            return None

    def process_google_sheet(self, sheet_url: str) -> List[Dict]:
        """
        Process a Google Sheet URL to fetch data.
        """
        try:
            # Define the scope for Google Sheets API
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

            # Authenticate using the service account credentials
            credentials = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
            client = gspread.authorize(credentials)

            # Open the Google Sheet by URL
            sheet = client.open_by_url(sheet_url)
            worksheet = sheet.get_worksheet(0)  # Get the first worksheet

            # Fetch all data from the worksheet
            data = worksheet.get_all_records()

            print(f"✅ Successfully fetched data from Google Sheet: {sheet_url}")
            return data

        except gspread.exceptions.SpreadsheetNotFound:
            print(f"❌ Google Sheet not found: {sheet_url}")
            return [{'error': 'Google Sheet not found', 'message': f'Invalid URL or permissions: {sheet_url}'}]
        except Exception as e:
            print(f"❌ Error processing Google Sheet: {e}")
            return [{'error': 'Unexpected error', 'message': str(e)}]
    
    def process_google_sheet_dataframe(self, df):
        results = []
        # Expect columns: A=Identifier, B=Address
        for row_num, row in enumerate(df.values, 0):
            if len(row) < 2 or not str(row[1]).strip():
                results.append({
                    'row': row_num,
                    'identifier': row[0] if len(row) > 0 else None,
                    'address': row[1] if len(row) > 1 else None,
                    'error': 'Missing address',
                })
                continue

            identifier = str(row[0]).strip() if len(row) > 0 else None
            address_string = str(row[1]).strip().strip('"')

            # Debug log for the address being processed
            print(f"\n📋 Processing Row {row_num}: {address_string}")

            # Parse the address string (format: "Street, City State ZIP")
            parts = address_string.split(',')
            if len(parts) < 2:
                results.append({
                    'row': row_num,
                    'identifier': identifier,
                    'address': address_string,
                    'error': 'Invalid format',
                    'message': 'Address must be in format: "Street, City State ZIP"'
                })
                continue

            street = parts[0].strip()
            city_state_zip = parts[1].strip()
            city_state_parts = city_state_zip.split()

            if len(city_state_parts) < 2:
                results.append({
                    'row': row_num,
                    'identifier': identifier,
                    'address': address_string,
                    'error': 'Invalid format',
                    'message': 'Must include city and state'
                })
                continue

            state = city_state_parts[-2]
            zip_code = city_state_parts[-1] if city_state_parts[-1].isdigit() else None
            city = ' '.join(city_state_parts[:-2]) if zip_code else ' '.join(city_state_parts[:-1])

            # Debug log for parsed components
            print(f"Parsed Address - Street: {street}, City: {city}, State: {state}, ZIP: {zip_code}")

            # Call lookup_address and log the result
            lookup_result = self.lookup_address(street, city, state, zip_code)
            print(f"Row {row_num}: Lookup Result: {lookup_result}")

            ffiec_result = self.get_ffiec_income_level(lookup_result.get('address'), lookup_result.get('census_geography', {}))

            result = {
                'row': row_num,
                'identifier': identifier,
                'address': address_string,
                'ffiec_income_level': ffiec_result.get('ffiec_income_level', None),
                'error': lookup_result.get('error', None)
            }
            results.append(result)
        return results
    
    def update_google_sheet(self, sheet_url: str, results: List[Dict]) -> None:
        """
        Update the Google Sheet with the income results.
        """
        try:
            # Define the scope for Google Sheets API
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

            # Authenticate using the service account credentials
            credentials = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
            client = gspread.authorize(credentials)

            # Open the Google Sheet by URL
            sheet = client.open_by_url(sheet_url)
            worksheet = sheet.get_worksheet(0)  # Get the first worksheet

            # Write results back to the sheet
            for i, result in enumerate(results, start=2):  # Start from row 2 (assuming row 1 is headers)
                income_level = result.get('ffiec_income_level', 'N/A')
                worksheet.update_cell(i, 3, income_level)  # Write to column C

            print(f"✅ Successfully updated Google Sheet with results: {sheet_url}")

        except gspread.exceptions.SpreadsheetNotFound:
            print(f"❌ Google Sheet not found: {sheet_url}")
        except Exception as e:
            print(f"❌ Error updating Google Sheet: {e}")

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description='Look up Census demographics for an address')
    parser.add_argument('address', nargs='?', help='Street address')
    parser.add_argument('city', nargs='?', help='City name')
    parser.add_argument('state', nargs='?', help='State name or abbreviation')
    parser.add_argument('--zip', help='ZIP code (optional)')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    parser.add_argument('--batch', help='Process addresses from CSV file (e.g., "Address Inputs/address_input.csv")')
    parser.add_argument('--google-api-key', help='Google Maps API key for enhanced geocoding (optional)')
    parser.add_argument('--no-fuzzy', action='store_true', help='Disable fuzzy address matching')
    parser.add_argument('--output-csv', nargs='?', const='', help='Save results to CSV file in Results folder (optional filename)')
    
    args = parser.parse_args()
    
    lookup = CensusDemographicsLookup(google_maps_api_key=args.google_api_key)
    
    # Handle batch processing
    if args.batch:
        results = lookup.process_csv_file(args.batch)
        
        # Save to CSV if requested
        if args.output_csv is not None:
            output_file = args.output_csv if args.output_csv else None
            csv_file = lookup.save_results_to_csv(results, output_file)
            if csv_file:
                print(f"✅ CSV output saved successfully")
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            lookup.print_batch_results(results)
        return
    
    # Handle single address processing
    if not args.address or not args.city or not args.state:
        print("❌ Error: Address, city, and state are required for single address lookup")
        print("   Use --batch for CSV file processing")
        return
    
    result = lookup.lookup_address(args.address, args.city, args.state, args.zip, use_fuzzy_matching=not args.no_fuzzy)
    
    # Save to CSV if requested
    if args.output_csv is not None:
        # Add row/column info for single address
        result['row'] = 1
        result['column'] = 1
        result['original_address'] = f"{args.address}, {args.city}, {args.state}" + (f" {args.zip}" if args.zip else "")
        
        output_file = args.output_csv if args.output_csv else None
        csv_file = lookup.save_results_to_csv([result], output_file)
        if csv_file:
            print(f"✅ CSV output saved successfully")
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        lookup.print_results(result)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Interactive mode
        print("🏠 Census Demographics Lookup Tool")
        print("=" * 40)
        
        lookup = CensusDemographicsLookup()
        
        while True:
            print("\nEnter address information:")
            address = input("Street Address: ").strip()
            if not address:
                break
                
            city = input("City: ").strip()
            state = input("State: ").strip()
            zip_code = input("ZIP Code (optional): ").strip() or None
            
            result = lookup.lookup_address(address, city, state, zip_code)
            lookup.print_results(result)
            
            print("\n" + "="*50)
            continue_lookup = input("Look up another address? (y/n): ")
            if continue_lookup.lower() != 'y':
                break
    else:
        main()