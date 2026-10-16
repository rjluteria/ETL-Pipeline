"""
loader.py

Do's:
    Opens the .xlsx file selected by the user, handles sheet
    selection if there are multiple sheets, and checks that all
    required columns are present before passing the data forward.

Dont's:
    - Any data cleaning or filtering
    - Any UI logic outside of sheet selection and validation errors
"""

import pandas as pd
import tkinter as tk
from tkinter import messagebox


REQUIRED_COLUMNS = [
    "Charging Station Name",
    "Customer Name",
    "Start Time",
    "End Time",
    "Duration",
    "Energy Consumed (kWh)",
    "Amount",
    "Transaction No."
]


def _pick_sheet(sheet_names):
    # If only one sheet exists, return it immediately
    if len(sheet_names) == 1:
        return sheet_names[0]

    result = {"choice": None}

    popup = tk.Toplevel()
    popup.title("Select Sheet")
    popup.geometry("300x300")
    popup.resizable(False, False)
    popup.grab_set()

    tk.Label(popup, text="Multiple sheets found.\nSelect the sheet to process:", font=("Arial", 10)).pack(pady=(16, 8))

    listbox = tk.Listbox(popup, width=35, height=8)
    listbox.pack(padx=16, pady=4)
    for s in sheet_names:
        listbox.insert(tk.END, s)

    def on_select():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a sheet.", parent=popup)
            return
        result["choice"] = sheet_names[sel[0]]
        popup.destroy()

    def on_cancel():
        popup.destroy()

    btn_row = tk.Frame(popup)
    btn_row.pack(pady=8)
    tk.Button(btn_row, text="Select", width=12, command=on_select).pack(side="left", padx=6)
    tk.Button(btn_row, text="Cancel", width=12, command=on_cancel).pack(side="left", padx=6)

    popup.wait_window()
    return result["choice"]


def load_file(file_path):
    # Open the Excel file and get all sheet names
    xl = pd.ExcelFile(file_path)
    sheet_names = xl.sheet_names

    # Let the user pick a sheet if there are multiple
    sheet = _pick_sheet(sheet_names)
    if sheet is None:
        return None

    # Read without assuming header row position
    raw = pd.read_excel(file_path, sheet_name=sheet, header=None)
    if raw.empty:
        messagebox.showerror("Empty File", "The selected sheet contains no data.")
        return None

    # Search for the header row by looking for "Charging Station Name"
    header_row_idx = None
    for i, row in raw.iterrows():
        if "Charging Station Name" in row.values:
            header_row_idx = i
            break
    if header_row_idx is None:
        messagebox.showerror("Validation Failed",
            "Could not find the header row.\n\nExpected 'Charging Station Name'.")
        return None

    # Set the header row and drop everything above it
    df = raw.iloc[header_row_idx:].reset_index(drop=True)
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)

    # Check for duplicate column names
    dupes = [c for c in df.columns if list(df.columns).count(c) > 1]
    if dupes:
        messagebox.showerror("Validation Failed", f"Duplicate column names:\n{', '.join(set(dupes))}")
        return None

    # Check for missing or misnamed columns
    col_map = {c.lower(): c for c in df.columns}
    missing, suggestions = [], []
    for req in REQUIRED_COLUMNS:
        if req not in df.columns:
            if req.lower() in col_map:
                suggestions.append(f"  '{req}' found as '{col_map[req.lower()]}'")
            else:
                missing.append(req)
    if suggestions:
        messagebox.showerror("Validation Failed", "Column name casing mismatch:\n" + "\n".join(suggestions))
        return None
    if missing:
        messagebox.showerror("Validation Failed", f"Missing columns:\n{', '.join(missing)}")
        return None

    return df