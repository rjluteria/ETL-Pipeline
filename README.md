# ETL Pipeline

A desktop tool that turns raw EV charging records into organized Excel reports. It automates repetitive cleaning, filtering, and reporting tasks through a simple interface.

## What it does

- Cleans duplicate and invalid charging records.
- Filters data by customer group, station, and payment status.
- Adds station location information.
- Generates formatted Excel reports, session counts, and utilization summaries.
- Creates billing reports using configurable filters.

## How it works

Select a workbook, choose your filters, and generate a report. Station mappings, customer groups, charging points, and billing filters can be managed through the interface.

Files are processed locally. No API keys or cloud services are required.

## Quick start

Requires Python 3.10+ with Tkinter.

```bash
git clone https://github.com/rjluteria/ETL-Pipeline.git
cd ETL-Pipeline
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy `config.example.json` to `config.json`, replace the fictional settings with your own, then launch:

```bash
python main.py
```

## Input and output

Accepts `.xlsx` and `.xls` workbooks with charging-session records.

Required columns:

- Charging Station Name
- Customer Name
- Start Time
- End Time
- Duration
- Energy Consumed (kWh)
- Amount
- Transaction No.

Standard reports also require `Charger Type`. Include `Charging Point ID` and `Plug Type` for charging-point utilization details.

Reports are saved to your Downloads folder. Standard output includes four sheets: **Charge Data**, **Counter**, **Utilization Rate**, and **Detailed Counter**. Billing output contains a **Prepped** sheet.

Existing reports with the same filename are overwritten.

## Configuration

`config.json` controls station locations, customer groups, charging points, billing filters, excluded stations, the cutoff date, and station-name normalization.

The example configuration contains fictional entries. Your real configuration stays excluded from Git.

## Built with

Python · pandas · openpyxl · Tkinter

The code separates data loading, cleaning, mapping, reporting, configuration, and interface components.

## Notes

- Designed for a specific charging-session spreadsheet format.
- Requires a graphical desktop and an existing Downloads folder.
- Keep real customer data, business configuration, and generated reports out of public commits.
