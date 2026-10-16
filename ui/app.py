"""
app.py

Do's:
    Creates the root window, all screen frames, and shared state.
    Wires all screens and managers together and starts the app.

Don'ts:
    - Any ETL logic
    - Any screen content (that's in screens/)
    - Any manager popups (that's in managers/)
"""

import tkinter as tk
from core.runner import run_etl, run_billing_etl
from ui.screens.main_screen import build_main_screen
from ui.screens.groups_screen import build_groups_screen
from ui.screens.stations_screen import build_stations_screen
from ui.screens.mapped_screen import build_mapped_screen
from ui.screens.amount_screen import build_amount_screen

# Root window
root = tk.Tk()
root.title("ETL Tool")
root.geometry("300x460")
root.resizable(False, False)

# Shared state — carries data between screens
pending_context = {}

# Frames — one per screen
main_frame    = tk.Frame(root)
group_frame   = tk.Frame(root)
station_frame = tk.Frame(root)
mapped_frame  = tk.Frame(root)
amount_frame  = tk.Frame(root)

all_frames = [main_frame, group_frame, station_frame, mapped_frame, amount_frame]


def hide_all():
    # Hide all frames before showing a new screen
    for f in all_frames:
        f.pack_forget()

def show_main():
    hide_all()
    pending_context.clear()
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

def show_groups():
    hide_all()
    refresh_group_buttons()
    group_frame.pack(fill="both", expand=True, padx=20, pady=20)

def show_stations():
    hide_all()
    build_station_filter()
    station_frame.pack(fill="both", expand=True, padx=10, pady=10)

def show_mapped(back_target):
    hide_all()
    pending_context["back_from_mapped"] = back_target
    mapped_frame.pack(fill="both", expand=True, padx=20, pady=20)

def show_amount(back_target):
    hide_all()
    pending_context["back_from_amount"] = back_target
    amount_frame.pack(fill="both", expand=True, padx=20, pady=20)


# Navigation dict — passed into each screen so they can trigger navigation
nav = {
    "show_main":     show_main,
    "show_groups":   show_groups,
    "show_stations": show_stations,
    "show_mapped":   show_mapped,
    "show_amount":   show_amount,
}

# Build each screen — each returns any callbacks app.py needs
refresh_group_buttons = build_groups_screen(
    group_frame, pending_context, nav, root, all_frames, run_etl
)

build_station_filter = build_stations_screen(
    station_frame, pending_context, nav
)

build_mapped_screen(
    mapped_frame, pending_context, nav
)

build_amount_screen(
    amount_frame, pending_context, nav, root, all_frames, run_etl
)

build_main_screen(
    main_frame, pending_context, nav, root, all_frames,
    run_etl, run_billing_etl,
    refresh_group_buttons, show_groups
)

# Start the app
show_main()
root.mainloop()