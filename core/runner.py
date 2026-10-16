"""
runner.py

Do's:
    Orchestrates the full ETL pipeline by calling the loader,
    filters, and transformer in order. Handles all ETL modes —
    clean, mapped, user groups, stations, and billing.

Dont's:
    - Any data cleaning or filtering logic
    - Any transformation logic
    - Any UI logic outside of unknown station prompts
    - Any output writing
"""

import platform
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

from core.loader import load_file
from core.filters import apply_filters
from core.transformer import map_station_locations
from config.config_manager import get_groups, get_billing, get_stations, save_stations
from output.writer import write_output, write_billing_output

etl_running = False

_DAY_FORMAT = "%-d" if platform.system() != "Windows" else "%#d"


def _fmt_datetime(x):
    if pd.notna(x):
        hour = str(int(x.strftime("%I")))
        month = x.strftime("%B")
        day   = x.strftime(f"{_DAY_FORMAT}")
        year  = x.strftime("%Y")
        time  = x.strftime(f"{hour}:%M:%S")
        ampm  = x.strftime("%p").upper()
        return f'="{month} {day}, {year} {time} {ampm}"'
    return ""

def _normalize_name(name):
    # Normalize a customer name to "Last, First" format
    if pd.isna(name):
        return ""
    name = str(name).strip()
    parts = name.split(",", 1)
    if len(parts) == 2:
        return parts[0].strip() + ", " + parts[1].strip()
    return name


def _prompt_unknown_stations(unknowns, station_map):
    # Show a popup for each unknown station so the user can add its location data
    for station in unknowns:
        popup = tk.Toplevel()
        popup.title("Unknown Station")
        popup.geometry("400x280")
        popup.grab_set()
        popup.resizable(False, False)

        tk.Label(popup, text="Unknown station found:", font=("Arial", 10)).pack(pady=(16, 0))
        tk.Label(popup, text=station, font=("Arial", 11, "bold")).pack(pady=(2, 12))

        frame = tk.Frame(popup)
        frame.pack(padx=24, fill="x")

        fields = {}
        for label in ["City", "Province", "Region", "Country"]:
            row = tk.Frame(frame)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{label}:", width=10, anchor="w").pack(side="left")
            entry = tk.Entry(row, width=28)
            entry.pack(side="left")
            fields[label] = entry

        fields["Country"].insert(0, "Philippines")

        def on_save():
            city     = fields["City"].get().strip()
            province = fields["Province"].get().strip()
            region   = fields["Region"].get().strip()
            country  = fields["Country"].get().strip()
            if not all([city, province, region, country]):
                messagebox.showwarning("Missing Info", "Please fill in all fields.", parent=popup)
                return
            station_map[station] = [city, province, region, country]
            save_stations(station_map)
            popup.destroy()

        def on_skip():
            popup.destroy()

        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=14)
        tk.Button(btn_frame, text="Save & Continue", width=16, command=on_save).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Skip", width=10, command=on_skip).pack(side="left", padx=6)

        popup.wait_window()


def _set_all_buttons(root, frames, state):
    # Disable or enable all buttons across all frames
    for frame in [root] + frames:
        for widget in frame.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=state)


def run_etl(mode_label, group_names=None, use_blacklist=False, station_filter=None, amount_filter=None, use_mapping=True, root=None, frames=None):
    global etl_running
    if etl_running:
        return

    etl_running = True
    if root and frames:
        _set_all_buttons(root, frames, "disabled")

    try:
        _run_etl_inner(mode_label, group_names, use_blacklist, station_filter, amount_filter, use_mapping)
    except Exception as e:
        messagebox.showerror("ETL Error", f"An unexpected error occurred:\n{str(e)}")
    finally:
        etl_running = False
        if root and frames:
            _set_all_buttons(root, frames, "normal")


def _run_etl_inner(mode_label, group_names=None, use_blacklist=False, station_filter=None, amount_filter=None, use_mapping=True):
    # Step 1: Open file dialog
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
    if not file_path:
        return

    # Step 2: Load and validate
    df = load_file(file_path)
    if df is None:
        return

    # Step 3: Apply common filters
    result = apply_filters(df)
    if result is None:
        return
    df, start_dt, end_dt, valid_months = result

    # Step 4: Location mapping
    if use_mapping:
        stations = get_stations()
        df = map_station_locations(df, stations)
        unknowns = df[df["City"] == ""]["Charging Station Name"].dropna().unique().tolist()
        if unknowns:
            _prompt_unknown_stations(unknowns, stations)
            df = map_station_locations(df, stations)
    else:
        df = df.drop(columns=["City", "Province", "Region", "Country"], errors="ignore")

    # Step 5: Insert Year/Month columns after Customer Name
    cust_idx = list(df.columns).index("Customer Name")
    for col in ["Month", "Year"][::-1]:
        df.insert(cust_idx + 1, col, "")

    # Step 6: Format datetimes
    df["Start Time"] = start_dt.apply(_fmt_datetime)
    df["End Time"]   = end_dt.apply(_fmt_datetime)
    df["Year"]       = start_dt.apply(lambda x: str(x.year) if pd.notna(x) else "")
    df["Month"]      = start_dt.apply(lambda x: x.strftime("%Y-%m") if pd.notna(x) else "")

    # Step 7: Normalize customer names
    normalized_source = df["Customer Name"].apply(_normalize_name)

    # Step 8: Customer filter
    if use_blacklist:
        all_groups = get_groups()
        blacklist  = set()
        for members in all_groups.values():
            blacklist.update(members)
        normalized_blacklist = {_normalize_name(n) for n in blacklist}
        df = df[~normalized_source.isin(normalized_blacklist)].reset_index(drop=True)
        normalized_source = df["Customer Name"].apply(_normalize_name)
    else:
        normalized_group = {_normalize_name(n) for n in group_names}
        df = df[normalized_source.isin(normalized_group)].reset_index(drop=True)
        normalized_source = df["Customer Name"].apply(_normalize_name)

    # Step 9: Station filter
    if station_filter:
        df = df[df["Charging Station Name"].isin(station_filter)].reset_index(drop=True)

    # Step 10: Amount filter
    numeric_amount = pd.to_numeric(
        df["Amount"].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    ).fillna(0)

    # Step 11: Filename dates
    valid_start = start_dt.dropna()
    if valid_months:
        valid_start = valid_start[valid_start.dt.to_period("M") >= valid_months[0]]
    earliest = valid_start.min()
    latest   = valid_start.max()

    # Enforce exact column order
    COLUMN_ORDER = [
        "Charging Station Name", "City", "Province", "Region", "Country",
        "Charger Type", "Charging Point ID", "Plug Type", "Transaction No.",
        "Customer Name", "Year", "Month", "EV Brand", "Model",
        "Start Time", "End Time", "Duration", "Energy Consumed (kWh)", "Amount"
    ]
    df = df[[c for c in COLUMN_ORDER if c in df.columns]]

    # Step 12: Write output
    if amount_filter == "both":
        df_paid   = df[numeric_amount > 0].reset_index(drop=True)
        df_unpaid = df[numeric_amount == 0].reset_index(drop=True)
        f1 = write_output(df_paid,   f"{mode_label} - Paid"   if mode_label else "Paid",   earliest, latest)
        f2 = write_output(df_unpaid, f"{mode_label} - Unpaid" if mode_label else "Unpaid", earliest, latest)
        saved = [f for f in [f1, f2] if f]
        if saved:
            messagebox.showinfo("ETL Complete", "Saved:\n" + "\n".join(saved))
    else:
        if amount_filter == "paid":
            df = df[numeric_amount > 0].reset_index(drop=True)
        elif amount_filter == "unpaid":
            df = df[numeric_amount == 0].reset_index(drop=True)
        fname = write_output(df, mode_label, earliest, latest)
        if fname:
            messagebox.showinfo("ETL Complete", f"Saved: {fname}")


def run_billing_etl(root=None, frames=None):
    global etl_running
    if etl_running:
        return

    etl_running = True
    if root and frames:
        _set_all_buttons(root, frames, "disabled")

    try:
        _run_billing_inner()
    except Exception as e:
        messagebox.showerror("ETL Error", f"An unexpected error occurred:\n{str(e)}")
    finally:
        etl_running = False
        if root and frames:
            _set_all_buttons(root, frames, "normal")


def _run_billing_inner():
    # Step 1: Open file dialog
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
    if not file_path:
        return

    # Step 2: Load and validate
    df = load_file(file_path)
    if df is None:
        return

    # Step 3: Apply common filters
    result = apply_filters(df)
    if result is None:
        return
    df, start_dt, end_dt, valid_months = result

    # Step 4: Format datetimes
    df["Start Time"] = start_dt.apply(_fmt_datetime)
    df["End Time"]   = end_dt.apply(_fmt_datetime)
    df["Year"]       = start_dt.apply(lambda x: str(x.year) if pd.notna(x) else "")
    df["Month"]      = start_dt.apply(lambda x: x.strftime("%Y-%m") if pd.notna(x) else "")

    # Step 5: Normalize customer names
    df["Customer Name"] = df["Customer Name"].apply(_normalize_name)

    # Step 6: Drop location columns — no mapping for billing
    df = df.drop(columns=["City", "Province", "Region", "Country"], errors="ignore")

    # Step 7: Apply billing filter
    billing_config    = get_billing()
    billing_stations  = set(billing_config.get("stations", []))
    billing_customers = billing_config.get("customers", [])

    def matches_billing(row):
        station  = str(row.get("Charging Station Name", "")).strip()
        customer = str(row.get("Customer Name", "")).strip()
        if station in billing_stations:
            return True
        if any(kw.lower() in customer.lower() for kw in billing_customers):
            return True
        return False

    df = df[df.apply(matches_billing, axis=1)].reset_index(drop=True)

    if df.empty:
        messagebox.showerror("No Data", "No rows matched the billing filter.\n\nThe output file was not saved.")
        return

    # Step 8: Filename dates
    valid_start = start_dt.dropna()
    if valid_months:
        valid_start = valid_start[valid_start.dt.to_period("M") >= valid_months[0]]
    earliest = valid_start.min()
    latest   = valid_start.max()

    # Step 9: Enforce column order
    COLUMN_ORDER = [
        "Charging Station Name", "Charger Type", "Charging Point ID", "Plug Type",
        "Transaction No.", "Customer Name", "Year", "Month", "EV Brand", "Model",
        "Start Time", "End Time", "Duration", "Energy Consumed (kWh)", "Amount"
    ]
    df = df[[c for c in COLUMN_ORDER if c in df.columns]]

    # Step 10: Write billing output
    fname = write_billing_output(df, earliest, latest)
    if fname:
        messagebox.showinfo("Billing Complete", f"Saved: {fname}")