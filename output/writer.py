"""
writer.py

Do's:
    Takes the final dataframe and writes it to Excel.
    Produces the standard output and billing output files
    in the exact same format as the original tool.

Dont's:
    - Any data cleaning or filtering
    - Any transformation logic
    - Any UI logic
"""

import os
import platform
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
from config.config_manager import get_charging_points


# Date format — handles Mac vs Windows difference
_DAY_FORMAT = "%-d" if platform.system() != "Windows" else "%#d"


def _duration_to_seconds(val):
    # Converts a duration value (HH:MM:SS string or number) to total seconds
    try:
        if isinstance(val, str) and ":" in val:
            parts = val.strip().split(":")
            h, m, s = int(parts[0]), int(parts[1]), int(float(parts[2]))
            return h * 3600 + m * 60 + s
        return float(val)
    except Exception:
        return 0


def _format_sheet(ws, station_col=None, util_col=None):
    # Applies formatting to a worksheet: bold headers, auto column width, alignment
    center = Alignment(horizontal="center", vertical="center")
    left   = Alignment(horizontal="left",   vertical="center")
    bold   = Font(bold=True)

    for col_idx, col_cells in enumerate(ws.columns, 1):
        col_letter = get_column_letter(col_idx)
        header_cell = ws.cell(row=1, column=col_idx)
        header_cell.font = bold
        header_cell.alignment = center

        max_len = 0
        for cell in col_cells:
            try:
                cell_len = len(str(cell.value)) if cell.value is not None else 0
                max_len = max(max_len, cell_len)
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max_len + 4, 50)

        for row_idx in range(2, ws.max_row + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            if station_col and col_idx == station_col:
                cell.alignment = left
            else:
                cell.alignment = center

        if util_col and col_idx == util_col:
            for row_idx in range(2, ws.max_row + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.number_format = "0.00%"
                if cell.value is not None:
                    try:
                        cell.value = float(cell.value) / 100
                    except Exception:
                        pass


def _format_filename(earliest, latest, label=None):
    # Builds the output filename based on the date range and label
    prefix = f"Report({label})" if label else "Report"
    if earliest.year == latest.year:
        if earliest.month == latest.month:
            return f"{prefix}_{earliest.strftime('%B')}"
        return f"{prefix}_{earliest.strftime('%B')}-{latest.strftime('%B')}"
    return f"{prefix}_{earliest.strftime('%B %Y')}-{latest.strftime('%B %Y')}"


def write_output(df_out, label, earliest, latest):
    # Writes the standard 4-sheet Excel output file
    if df_out.empty:
        return None

    cp_data = get_charging_points()

    wb = Workbook()

    # ---- Sheet 1: Charge Data ----
    ws1 = wb.active
    ws1.title = "Charge Data"

    df_save = df_out.copy()
    df_save["Amount"] = pd.to_numeric(
        df_save["Amount"].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )

    headers = list(df_save.columns)
    for col_idx, header in enumerate(headers, 1):
        ws1.cell(row=1, column=col_idx, value=header)
    for row_idx, row in enumerate(df_save.itertuples(index=False), 2):
        for col_idx, value in enumerate(row, 1):
            ws1.cell(row=row_idx, column=col_idx, value=value)
    _format_sheet(ws1, station_col=1)

    # ---- Sheet 2: Counter ----
    ws2 = wb.create_sheet("Counter")

    df_dur = df_out.copy()
    df_dur["_seconds"] = df_dur["Duration"].apply(_duration_to_seconds)
    df_short = df_dur[df_dur["_seconds"] < 300]

    counter_headers = ["Charging Station Name", "Charger Type", "Duration Count (< 5 mins)", "Total Session Count"]
    for col_idx, h in enumerate(counter_headers, 1):
        ws2.cell(row=1, column=col_idx, value=h).font = Font(bold=True)

    row_num = 2
    for ct in ["AC", "DC"]:
        stations_in_ct = df_out[df_out["Charger Type"] == ct]["Charging Station Name"].unique()
        for station in stations_in_ct:
            dur_count   = len(df_short[(df_short["Charging Station Name"] == station) & (df_short["Charger Type"] == ct)])
            total_count = len(df_out[(df_out["Charging Station Name"] == station) & (df_out["Charger Type"] == ct)])
            ws2.cell(row=row_num, column=1, value=station)
            ws2.cell(row=row_num, column=2, value=ct)
            ws2.cell(row=row_num, column=3, value=dur_count)
            ws2.cell(row=row_num, column=4, value=total_count)
            row_num += 1
        row_num += 1

    _format_sheet(ws2, station_col=1)

    # ---- Sheet 3: Utilization Rate ----
    ws3 = wb.create_sheet("Utilization Rate")

    util_headers = ["Charging Station Name", "Charging Point ID", "Plug Type", "Charger Type", "Utilization Rate (%)"]
    for col_idx, h in enumerate(util_headers, 1):
        ws3.cell(row=1, column=col_idx, value=h).font = Font(bold=True)

    try:
        date_range_days = (latest - earliest).days + 1
    except Exception:
        date_range_days = 1

    cp_duration_map = {}
    for _, row in df_out.iterrows():
        cp  = str(row.get("Charging Point ID", "")).strip()
        dur = _duration_to_seconds(row.get("Duration", 0))
        cp_duration_map[cp] = cp_duration_map.get(cp, 0) + dur

    cp_info_map = {}
    for _, row in df_out.iterrows():
        cp = str(row.get("Charging Point ID", "")).strip()
        if cp and cp not in cp_info_map:
            cp_info_map[cp] = {
                "plug_type":    str(row.get("Plug Type", "")).strip(),
                "charger_type": str(row.get("Charger Type", "")).strip(),
            }

    stations_in_data = df_out["Charging Station Name"].unique().tolist()

    row_num = 2
    for station in stations_in_data:
        cp_entries = cp_data.get(station, [])
        if not cp_entries:
            continue
        first = True
        for cp_entry in cp_entries:
            cp_id      = cp_entry["cp_id"]
            active_hrs = cp_entry["active_hrs"]
            info       = cp_info_map.get(cp_id, {})
            plug_type  = info.get("plug_type", "")
            ct         = info.get("charger_type", "")

            total_active_secs = active_hrs * date_range_days * 3600
            total_used_secs   = cp_duration_map.get(cp_id, 0)
            util_rate = round((total_used_secs / total_active_secs) * 100, 2) if total_active_secs > 0 else 0

            ws3.cell(row=row_num, column=1, value=station if first else "")
            ws3.cell(row=row_num, column=2, value=cp_id)
            ws3.cell(row=row_num, column=3, value=plug_type)
            ws3.cell(row=row_num, column=4, value=ct)
            ws3.cell(row=row_num, column=5, value=util_rate)
            row_num += 1
            first = False

    _format_sheet(ws3, station_col=1, util_col=5)

    # ---- Sheet 4: Detailed Counter ----
    ws4 = wb.create_sheet("Detailed Counter")

    detail_cols = [
        "Charging Station Name", "Charger Type", "Charging Point ID",
        "Plug Type", "Transaction No.", "Customer Name",
        "Start Time", "End Time", "Duration",
        "Energy Consumed (kWh)", "Amount"
    ]

    df_detail = df_short[[c for c in detail_cols if c in df_short.columns]].copy()
    df_detail["Amount"] = pd.to_numeric(
        df_detail["Amount"].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )

    for col_idx, h in enumerate(detail_cols, 1):
        if h in df_detail.columns:
            ws4.cell(row=1, column=col_idx, value=h).font = Font(bold=True)
    for row_idx, row in enumerate(df_detail.itertuples(index=False), 2):
        for col_idx, value in enumerate(row, 1):
            ws4.cell(row=row_idx, column=col_idx, value=value)
    _format_sheet(ws4, station_col=1)

    fname = _format_filename(earliest, latest, label) + ".xlsx"
    fpath = os.path.join(os.path.expanduser("~/Downloads"), fname)
    wb.save(fpath)
    return fname


def write_billing_output(df_out, earliest, latest):
    # Writes the billing-specific Excel output file
    if df_out.empty:
        return None

    wb = Workbook()
    ws = wb.active
    ws.title = "Prepped"

    df_save = df_out.copy()
    df_save["Amount"] = pd.to_numeric(
        df_save["Amount"].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )

    headers = list(df_save.columns)
    center = Alignment(horizontal="center", vertical="center")
    left   = Alignment(horizontal="left",   vertical="center")
    bold   = Font(bold=True)

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = bold
        cell.alignment = center

    for row_idx, row in enumerate(df_save.itertuples(index=False), 2):
        for col_idx, value in enumerate(row, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = left if col_idx == 1 else center

    for col_idx in range(1, len(headers) + 1):
        col_letter = get_column_letter(col_idx)
        max_len = max(
            (len(str(ws.cell(row=r, column=col_idx).value or "")) for r in range(1, ws.max_row + 1)),
            default=10
        )
        ws.column_dimensions[col_letter].width = min(max_len + 4, 50)

    def _fmt_billing_filename(start, end):
        if start.year == end.year:
            if start.month == end.month:
                return f"Prepped Data (Billing)_{start.strftime('%B')}"
            return f"Prepped Data (Billing)_{start.strftime('%B')}-{end.strftime('%B')}"
        return f"Prepped Data (Billing)_{start.strftime('%B %Y')}-{end.strftime('%B %Y')}"

    fname = _fmt_billing_filename(earliest, latest) + ".xlsx"
    fpath = os.path.join(os.path.expanduser("~/Downloads"), fname)
    wb.save(fpath)
    return fname