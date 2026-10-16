"""
stations_screen.py

Do's:
    Builds the Stations filter screen. Shows a searchable list of
    checkboxes for each station. Passes selected stations to the
    next screen via pending_context.

Dont's:
    - Any ETL logic
    - Any station management (that's in managers/station_manager.py)
    - Any navigation logic (that's in app.py)
"""

import tkinter as tk
from tkinter import messagebox
from config.config_manager import get_stations


def build_stations_screen(frame, pending_context, nav):
    tk.Label(frame, text="Stations", font=("Arial", 13, "bold")).pack(pady=(0, 6))

    # Search box
    search_var = tk.StringVar()
    tk.Entry(frame, textvariable=search_var, width=32).pack(pady=(0, 4))

    # Scrollable list of checkboxes
    list_frame = tk.Frame(frame)
    list_frame.pack(fill="both", expand=True)

    canvas_sf    = tk.Canvas(list_frame, highlightthickness=0, height=200)
    scrollbar_sf = tk.Scrollbar(list_frame, orient="vertical", command=canvas_sf.yview)
    canvas_sf.configure(yscrollcommand=scrollbar_sf.set)

    inner_frame = tk.Frame(canvas_sf)
    inner_frame.bind("<Configure>", lambda e: canvas_sf.configure(scrollregion=canvas_sf.bbox("all")))
    canvas_sf.create_window((0, 0), window=inner_frame, anchor="nw")
    canvas_sf.pack(side="left", fill="both", expand=True)
    scrollbar_sf.pack(side="right", fill="y")

    # Mousewheel scrolling
    def _on_mousewheel(event):
        canvas_sf.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas_sf.bind("<Enter>", lambda e: canvas_sf.bind_all("<MouseWheel>", _on_mousewheel))
    canvas_sf.bind("<Leave>", lambda e: canvas_sf.unbind_all("<MouseWheel>"))

    station_vars = {}

    def build_station_filter():
        # Clear and rebuild checkboxes from current config
        for widget in inner_frame.winfo_children():
            widget.destroy()
        station_vars.clear()
        search_var.set("")
        for name in sorted(get_stations().keys()):
            var = tk.BooleanVar(value=False)
            station_vars[name] = var
            tk.Checkbutton(inner_frame, text=name, variable=var, anchor="w", width=30).pack(fill="x", padx=4, pady=1)

    def filter_stations(*args):
        # Show only stations matching the search query
        query = search_var.get().lower()
        for widget in inner_frame.winfo_children():
            if query in widget.cget("text").lower():
                widget.pack(fill="x", padx=4, pady=1)
            else:
                widget.pack_forget()

    search_var.trace_add("write", filter_stations)

    def on_run_stations():
        selected = {name for name, var in station_vars.items() if var.get()}
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one station.")
            return
        pending_context["station_filter"] = selected
        pending_context["station_label"]  = list(selected)[0] if len(selected) == 1 else "Stations"
        nav["show_mapped"](nav["show_stations"])

    tk.Frame(frame, height=1, bg="gray").pack(fill="x", pady=6)
    tk.Button(frame, text="Run ETL", width=28, command=on_run_stations).pack(pady=4)
    tk.Button(frame, text="← Back",  width=28, command=nav["show_main"]).pack(pady=4)

    # Return build_station_filter so app.py can call it when navigating to this screen
    return build_station_filter