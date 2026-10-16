"""
main_screen.py

Do's:
    Builds the main menu screen with all navigation and ETL buttons.

Dont's:
    - Any ETL logic
    - Any navigation logic (that's in app.py)
    - Any manager popups (that's in managers/)
"""

import tkinter as tk
from ui.managers.group_manager import open_group_manager
from ui.managers.station_manager import open_station_manager
from ui.managers.cp_manager import open_cp_manager
from ui.managers.billing_manager import open_billing_manager


def build_main_screen(frame, pending_context, nav, root, all_frames, run_etl, run_billing_etl, refresh_group_buttons, show_groups, build_station_filter=None):
    tk.Label(frame, text="ETL Tool", font=("Arial", 13, "bold")).pack(pady=(0, 12))

    def on_clean_data():
        pending_context["use_mapping"] = False
        pending_context["mode"] = "clean"
        nav["show_amount"](nav["show_main"])

    def on_mapped_data():
        pending_context["use_mapping"] = True
        pending_context["mode"] = "mapped"
        nav["show_amount"](nav["show_main"])

    tk.Button(frame, text="Clean Data",  width=28, command=on_clean_data).pack(pady=4)
    tk.Button(frame, text="Mapped Data", width=28, command=on_mapped_data).pack(pady=4)

    tk.Frame(frame, height=1, bg="gray").pack(fill="x", pady=10)

    tk.Button(frame, text="User Groups", width=28, command=show_groups).pack(pady=4)
    tk.Button(frame, text="Stations",    width=28, command=nav["show_stations"]).pack(pady=4)
    tk.Button(frame, text="Billing",     width=28, command=lambda: run_billing_etl(root=root, frames=all_frames)).pack(pady=4)

    tk.Frame(frame, height=1, bg="gray").pack(fill="x", pady=10)

    tk.Button(frame, text="Manage Groups",          width=28, command=lambda: open_group_manager(refresh_group_buttons)).pack(pady=4)
    tk.Button(frame, text="Manage Stations",        width=28, command=lambda: open_station_manager(build_station_filter)).pack(pady=4)
    tk.Button(frame, text="Manage Charging Points", width=28, command=open_cp_manager).pack(pady=4)
    tk.Button(frame, text="Manage Billing",         width=28, command=open_billing_manager).pack(pady=4)