import pandas as pd

# Load the datasets
gdp_df = pd.read_csv("gdp.csv", skiprows=4)         
gsp_df = pd.read_csv("gsp1997.csv")                 

# Keep only rows where the Description indicates total GDP in current dollars
gsp_df = gsp_df[gsp_df['Description'].str.contains("Current-dollar GDP", na=False)]

# Select only the state name and year columns
gsp_df = gsp_df.drop(columns=['GeoFIPS', 'Region', 'TableName', 'LineCode', 
                              'IndustryClassification', 'Unit', 'Description'])

# Rename for clarity
gsp_df = gsp_df.rename(columns={'GeoName': 'Name'})

# Convert wide format to long format: one row per (State, Year, GDP)
gsp_df = gsp_df.melt(id_vars='Name', var_name='Year', value_name='GDP')

# Clean up
gsp_df['Year'] = pd.to_numeric(gsp_df['Year'], errors='coerce')
gsp_df['GDP'] = pd.to_numeric(gsp_df['GDP'], errors='coerce')
gsp_df['Type'] = 'State'

# Drop bad rows
gsp_df = gsp_df.dropna(subset=['GDP', 'Year'])

# Keep only relevant columns from world GDP
gdp_df = gdp_df[['Country Name'] + [str(year) for year in range(1997, 2024)]]
gdp_df = gdp_df.melt(id_vars='Country Name', var_name='Year', value_name='GDP')
gdp_df = gdp_df.rename(columns={'Country Name': 'Name'})
gdp_df['Type'] = 'Country'

# Ensure correct data types in both datasets
gdp_df['Year'] = pd.to_numeric(gdp_df['Year'], errors='coerce')
gdp_df['GDP'] = pd.to_numeric(gdp_df['GDP'], errors='coerce')

gsp_df['Year'] = pd.to_numeric(gsp_df['Year'], errors='coerce')
gsp_df['GDP'] = pd.to_numeric(gsp_df['GDP'], errors='coerce')
gsp_df['Type'] = 'State'  # In case not already included

# Combine both datasets
combined_df = pd.concat([
    gdp_df[['Name', 'Year', 'GDP', 'Type']],
    gsp_df[['Name', 'Year', 'GDP', 'Type']]
], ignore_index=True)

# Drop rows with missing values
#combined_df = combined_df.dropna(subset=['GDP', 'Year'])

# Optional: save for reuse
combined_df.to_csv("combined_gdp_gsp.csv", index=False)