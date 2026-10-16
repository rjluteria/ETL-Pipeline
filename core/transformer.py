"""
transformer.py

Do's:
    Maps station names to their location data (City, Province,
    Region, Country) from config.

Dont's:
    - Loading or reading files
    - Any filtering or cleaning (that's filters.py)
    - Any UI logic
    - Any output writing
"""

import pandas as pd


def map_station_locations(df, station_map):
    # Add City, Province, Region, Country columns based on station name
    df[["City", "Province", "Region", "Country"]] = df["Charging Station Name"].apply(
        lambda x: pd.Series(station_map.get(x, ["", "", "", ""]))
    )
    return df