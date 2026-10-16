"""
filters.py

Do's:
    Takes the raw dataframe loaded from the Excel file and applies
    all cleaning and filtering logic. Returns a cleaned dataframe
    along with parsed datetime series and valid months.

Dont's:
    - Loading or reading files
    - Any mapping or name normalization (that's transformer.py)
    - Any UI logic
    - Any output writing
"""

import re
import pandas as pd
from config.config_manager import (
    get_station_blacklist,
    get_cutoff_date,
    get_station_normalization,
)


def apply_filters(df):
    # Remove blacklisted stations
    station_bl = set(get_station_blacklist())
    df = df[~df["Charging Station Name"].astype(str).str.strip().isin(station_bl)].reset_index(drop=True)

    # Normalize configured station name variants
    prefixes = tuple(name.casefold() for name in get_station_normalization())
    df["Charging Station Name"] = df["Charging Station Name"].astype(str).apply(
        lambda x: re.sub(r"\s*\(private\)\s*$", "", x, flags=re.IGNORECASE).strip()
        if prefixes and x.casefold().startswith(prefixes) else x
    )

    # Remove duplicate transactions
    df = df.drop_duplicates(subset="Transaction No.")

    # Parse datetimes once — carried through all remaining filters
    start_dt = pd.to_datetime(df["Start Time"], format="mixed", errors="coerce")
    end_dt   = pd.to_datetime(df["End Time"],   format="mixed", errors="coerce")

    # Clean Amount column
    df["Amount"] = df["Amount"].astype(str).str.replace("₱", "", regex=False).str.replace(",", "", regex=False).str.strip()

    # Remove zero/negative kWh rows
    mask_kwh = pd.to_numeric(df["Energy Consumed (kWh)"], errors="coerce").fillna(0) > 0
    df       = df[mask_kwh].reset_index(drop=True)
    start_dt = start_dt[mask_kwh].reset_index(drop=True)
    end_dt   = end_dt[mask_kwh].reset_index(drop=True)

    # Remove zero duration rows
    mask_dur = df["Duration"].astype(str).str.strip() != "00:00:00"
    df       = df[mask_dur].reset_index(drop=True)
    start_dt = start_dt[mask_dur].reset_index(drop=True)
    end_dt   = end_dt[mask_dur].reset_index(drop=True)

    # Remove impossible dates and rows before cutoff date
    cutoff     = pd.Timestamp(get_cutoff_date())
    mask_dates = (start_dt.dt.year >= 2000) & (start_dt >= cutoff)
    df         = df[mask_dates.values].reset_index(drop=True)
    start_dt   = start_dt[mask_dates].reset_index(drop=True)
    end_dt     = end_dt[mask_dates].reset_index(drop=True)

    # Remove previous month outliers (months with 5 or fewer records)
    valid_months = []
    if not start_dt.empty:
        unique_months = sorted(start_dt.dt.to_period("M").unique())
        month_counts  = start_dt.dt.to_period("M").value_counts()
        valid_months  = sorted([m for m in unique_months if month_counts.get(m, 0) > 5])
        if valid_months:
            keep     = start_dt.dt.to_period("M") >= valid_months[0]
            df       = df[keep.values].reset_index(drop=True)
            start_dt = start_dt[keep].reset_index(drop=True)
            end_dt   = end_dt[keep].reset_index(drop=True)

    return df, start_dt, end_dt, valid_months