"""
station_manager.py

Do's:
    Opens the Manage Stations popup window. Handles adding, editing,
    and deleting stations. Supports import/export of station data.

Dont's:
    - Any ETL logic
    - Any screen navigation
    - Any other manager logic
"""

import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from config.config_manager import get_stations, save_stations


def open_station_manager(refresh_station_filter=None):
    station_map = get_stations()

    win = tk.Toplevel()
    win.title("Manage Stations")
    win.geometry("680x480")
    win.grab_set()
    win.protocol("WM_DELETE_WINDOW", lambda: [
        refresh_station_filter() if refresh_station_filter else None,
        win.destroy()
    ])

    # Toolbar buttons
    toolbar = tk.Frame(win)
    toolbar.pack(fill="x", padx=10, pady=(10, 0))

    tk.Button(toolbar, text="+ Add Station",   width=14, command=lambda: open_station_form(win, station_map, tree)).pack(side="left", padx=(0, 6))
    tk.Button(toolbar, text="Edit Selected",   width=14, command=lambda: edit_selected(win, station_map, tree)).pack(side="left", padx=(0, 6))
    tk.Button(toolbar, text="Delete Selected", width=14, command=lambda: delete_selected(station_map, tree)).pack(side="left", padx=(0, 20))
    tk.Button(toolbar, text="Export Stations", width=14, command=lambda: export_stations(win, station_map)).pack(side="right", padx=(6, 0))
    tk.Button(toolbar, text="Import Stations", width=14, command=lambda: import_stations(win, station_map, tree)).pack(side="right", padx=(6, 0))

    # Treeview with scrollbar
    cols = ("Station Name", "City", "Province", "Region", "Country")
    tree_frame = tk.Frame(win)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

    scrollbar = tk.Scrollbar(tree_frame)
    scrollbar.pack(side="right", fill="y")

    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", yscrollcommand=scrollbar.set)
    scrollbar.config(command=tree.yview)

    col_widths = [220, 100, 110, 70, 100]
    for col, w in zip(cols, col_widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="w")

    tree.pack(fill="both", expand=True)

    def refresh_tree(sm):
        # Rebuild the treeview from the station map
        tree.delete(*tree.get_children())
        for name, vals in sorted(sm.items()):
            tree.insert("", "end", values=(name, *vals))

    refresh_tree(station_map)

    def open_station_form(parent, sm, t, edit_name=None):
        form = tk.Toplevel(parent)
        form.title("Edit Station" if edit_name else "Add Station")
        form.geometry("400x260")
        form.grab_set()
        form.resizable(False, False)

        tk.Label(form, text="Station Name:").grid(row=0, column=0, sticky="w", padx=16, pady=8)
        name_entry = tk.Entry(form, width=32)
        name_entry.grid(row=0, column=1, pady=8)

        labels = ["City", "Province", "Region", "Country"]
        entries = {}
        for i, lbl in enumerate(labels, start=1):
            tk.Label(form, text=f"{lbl}:").grid(row=i, column=0, sticky="w", padx=16, pady=5)
            e = tk.Entry(form, width=32)
            e.grid(row=i, column=1, pady=5)
            entries[lbl] = e

        if edit_name:
            name_entry.insert(0, edit_name)
            name_entry.config(state="disabled")
            vals = sm.get(edit_name, ["", "", "", ""])
            for lbl, v in zip(labels, vals):
                entries[lbl].insert(0, v)
        else:
            entries["Country"].insert(0, "Philippines")

        def on_save():
            sname    = name_entry.get().strip() if not edit_name else edit_name
            city     = entries["City"].get().strip()
            province = entries["Province"].get().strip()
            region   = entries["Region"].get().strip()
            country  = entries["Country"].get().strip()
            if not all([sname, city, province, region, country]):
                messagebox.showwarning("Missing Info", "Please fill in all fields.", parent=form)
                return
            sm[sname] = [city, province, region, country]
            save_stations(sm)
            refresh_tree(sm)
            # Refresh station filter screen if it's currently visible
            if refresh_station_filter:
                refresh_station_filter()
            form.destroy()

        tk.Button(form, text="Save", width=12, command=on_save).grid(row=5, column=0, columnspan=2, pady=14)

    def edit_selected(parent, sm, t):
        selected = t.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a station to edit.")
            return
        name = t.item(selected[0])["values"][0]
        open_station_form(parent, sm, t, edit_name=name)

    def delete_selected(sm, t):
        selected = t.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a station to delete.")
            return
        name = t.item(selected[0])["values"][0]
        if messagebox.askyesno("Delete Station", f"Delete '{name}'?\n\nThis will also remove its Charging Points."):
            sm.pop(name, None)
            save_stations(sm)
            refresh_tree(sm)
            if refresh_station_filter:
                refresh_station_filter()

    def export_stations(parent, sm):
        dest = filedialog.asksaveasfilename(
            parent=parent, defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="stations.json", title="Export Stations"
        )
        if not dest:
            return
        try:
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(sm, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Export Complete", f"Stations exported to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def import_stations(parent, sm, t):
        src = filedialog.askopenfilename(
            parent=parent, filetypes=[("JSON files", "*.json")], title="Import Stations"
        )
        if not src:
            return
        try:
            with open(src, "r", encoding="utf-8") as f:
                imported = json.load(f)
            if not isinstance(imported, dict):
                raise ValueError("Invalid stations file format.")
            added = updated = 0
            for k, v in imported.items():
                if k in sm:
                    updated += 1
                else:
                    added += 1
                sm[k] = v
            save_stations(sm)
            refresh_tree(sm)
            messagebox.showinfo("Import Complete", f"Import successful.\nAdded: {added}  |  Updated: {updated}")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))