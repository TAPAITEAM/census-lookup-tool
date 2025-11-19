from census_demographics_lookup import CensusDemographicsLookup

lookup = CensusDemographicsLookup()
result = lookup.lookup_address("25 Drake Ave", "New Rochelle", "New York", "10805")
print(result)