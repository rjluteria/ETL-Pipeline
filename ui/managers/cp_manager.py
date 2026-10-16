"""
cp_manager.py

Do's:
    Opens the Manage Charging Points popup window. Syncs stations
    from config on open. Handles adding, editing, and deleting
    charging points per station. Supports import/export.

Dont's:
    - Any ETL logic
    - Any screen navigation
    - Any other manager logic
"""

import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from config.config_manager import get_charging_points, save_charging_points, read_config, save_config


def open_cp_manager():
    # Sync stations — ensure every station has a CP entry
    config   = read_config()
    stations = config.get("stations", {})
    cp_data  = config.get("charging_points", {})
    for station in stations:
        if station not in cp_data:
            cp_data[station] = []
    config["charging_points"] = cp_data
    save_config(config)
    cp_data = get_charging_points()

    win = tk.Toplevel()
    win.title("Manage Charging Points")
    win.geometry("680x520")
    win.grab_set()

    # Left panel — station list
    left = tk.Frame(win, width=220)
    left.pack(side="left", fill="y", padx=(10, 0), pady=10)

    tk.Label(left, text="Stations", font=("Arial", 10, "bold")).pack(anchor="w")

    station_list = tk.Listbox(left, width=26, height=20, exportselection=False)
    station_list.pack(fill="y", expand=True, pady=(4, 0))

    # Right panel — charging points treeview
    right = tk.Frame(win)
    right.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    tk.Label(right, text="Charging Points", font=("Arial", 10, "bold")).pack(anchor="w")

    cols = ("Charging Point ID", "Active Hours")
    tree_frame = tk.Frame(right)
    tree_frame.pack(fill="both", expand=True, pady=(4, 0))

    scrollbar = tk.Scrollbar(tree_frame)
    scrollbar.pack(side="right", fill="y")

    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", yscrollcommand=scrollbar.set)
    scrollbar.config(command=tree.yview)
    tree.heading("Charging Point ID", text="Charging Point ID")
    tree.heading("Active Hours",      text="Active Hours (hrs/day)")
    tree.column("Charging Point ID", width=200, anchor="w")
    tree.column("Active Hours",      width=120, anchor="center")
    tree.pack(fill="both", expand=True)

    cp_btn_row = tk.Frame(right)
    cp_btn_row.pack(fill="x", pady=(6, 0))
    add_cp_btn  = tk.Button(cp_btn_row, text="+ Add CP",  width=12)
    edit_cp_btn = tk.Button(cp_btn_row, text="Edit CP",   width=12)
    del_cp_btn  = tk.Button(cp_btn_row, text="Remove CP", width=12)
    add_cp_btn.pack(side="left")
    edit_cp_btn.pack(side="left", padx=4)
    del_cp_btn.pack(side="left")

    # Import / Export buttons
    ie_row = tk.Frame(win)
    ie_row.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
    tk.Button(ie_row, text="Import", width=12, command=lambda: import_cp(win, cp_data, refresh_all)).pack(side="left", padx=(0, 6))
    tk.Button(ie_row, text="Export", width=12, command=lambda: export_cp(win, cp_data)).pack(side="left")

    def refresh_station_list():
        station_list.delete(0, tk.END)
        for s in sorted(cp_data.keys()):
            station_list.insert(tk.END, s)
        refresh_cp_tree()
        update_btn_states()

    def refresh_cp_tree():
        # Rebuild CP treeview for the selected station
        tree.delete(*tree.get_children())
        sel = station_list.curselection()
        if sel:
            station = station_list.get(sel[0])
            for cp in cp_data.get(station, []):
                tree.insert("", "end", values=(cp["cp_id"], cp["active_hrs"]))
        update_btn_states()

    def update_btn_states():
        station_sel = bool(station_list.curselection())
        cp_sel      = bool(tree.selection())
        add_cp_btn.config(state="normal"  if station_sel else "disabled")
        edit_cp_btn.config(state="normal" if (station_sel and cp_sel) else "disabled")
        del_cp_btn.config(state="normal"  if (station_sel and cp_sel) else "disabled")

    station_list.bind("<<ListboxSelect>>", lambda e: refresh_cp_tree())
    tree.bind("<<TreeviewSelect>>",        lambda e: update_btn_states())

    def refresh_all():
        refresh_station_list()

    def on_add_cp():
        sel = station_list.curselection()
        if not sel:
            return
        station = station_list.get(sel[0])
        form = tk.Toplevel(win)
        form.title("Add Charging Point")
        form.geometry("340x160")
        form.grab_set()
        form.resizable(False, False)
        tk.Label(form, text="Charging Point ID:").grid(row=0, column=0, sticky="w", padx=16, pady=10)
        cp_entry = tk.Entry(form, width=24)
        cp_entry.grid(row=0, column=1, pady=10)
        tk.Label(form, text="Active Hours (hrs/day):").grid(row=1, column=0, sticky="w", padx=16, pady=6)
        hrs_entry = tk.Entry(form, width=24)
        hrs_entry.grid(row=1, column=1, pady=6)
        def save():
            cp_id = cp_entry.get().strip()
            try:
                hrs = int(hrs_entry.get().strip())
            except ValueError:
                messagebox.showwarning("Invalid", "Active Hours must be a number.", parent=form)
                return
            if not cp_id:
                messagebox.showwarning("Missing Info", "Please enter a Charging Point ID.", parent=form)
                return
            if any(c["cp_id"] == cp_id for c in cp_data.get(station, [])):
                messagebox.showwarning("Duplicate", f"'{cp_id}' already exists in this station.", parent=form)
                return
            cp_data.setdefault(station, []).append({"cp_id": cp_id, "active_hrs": hrs})
            save_charging_points(cp_data)
            refresh_cp_tree()
            form.destroy()
        tk.Button(form, text="Save", width=12, command=save).grid(row=2, column=0, columnspan=2, pady=12)

    def on_edit_cp():
        sel_s = station_list.curselection()
        sel_c = tree.selection()
        if not sel_s or not sel_c:
            return
        station   = station_list.get(sel_s[0])
        old_cp_id, old_hrs = tree.item(sel_c[0])["values"]
        form = tk.Toplevel(win)
        form.title("Edit Charging Point")
        form.geometry("340x160")
        form.grab_set()
        form.resizable(False, False)
        tk.Label(form, text="Charging Point ID:").grid(row=0, column=0, sticky="w", padx=16, pady=10)
        cp_entry = tk.Entry(form, width=24)
        cp_entry.insert(0, old_cp_id)
        cp_entry.config(state="disabled")
        cp_entry.grid(row=0, column=1, pady=10)
        tk.Label(form, text="Active Hours (hrs/day):").grid(row=1, column=0, sticky="w", padx=16, pady=6)
        hrs_entry = tk.Entry(form, width=24)
        hrs_entry.insert(0, old_hrs)
        hrs_entry.grid(row=1, column=1, pady=6)
        def save():
            try:
                hrs = int(hrs_entry.get().strip())
            except ValueError:
                messagebox.showwarning("Invalid", "Active Hours must be a number.", parent=form)
                return
            for cp in cp_data.get(station, []):
                if cp["cp_id"] == old_cp_id:
                    cp["active_hrs"] = hrs
                    break
            save_charging_points(cp_data)
            refresh_cp_tree()
            form.destroy()
        tk.Button(form, text="Save", width=12, command=save).grid(row=2, column=0, columnspan=2, pady=12)

    def on_del_cp():
        sel_s = station_list.curselection()
        sel_c = tree.selection()
        if not sel_s or not sel_c:
            return
        station = station_list.get(sel_s[0])
        cp_id   = tree.item(sel_c[0])["values"][0]
        if messagebox.askyesno("Remove CP", f"Remove '{cp_id}' from '{station}'?"):
            cp_data[station] = [c for c in cp_data[station] if c["cp_id"] != cp_id]
            save_charging_points(cp_data)
            refresh_cp_tree()

    add_cp_btn.config(command=on_add_cp)
    edit_cp_btn.config(command=on_edit_cp)
    del_cp_btn.config(command=on_del_cp)

    def export_cp(parent, data):
        dest = filedialog.asksaveasfilename(
            parent=parent, defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="chargingpoints.json", title="Export Charging Points"
        )
        if not dest:
            return
        try:
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Export Complete", f"Charging points exported to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def import_cp(parent, data, callback):
        src = filedialog.askopenfilename(
            parent=parent, filetypes=[("JSON files", "*.json")], title="Import Charging Points"
        )
        if not src:
            return
        try:
            with open(src, "r", encoding="utf-8") as f:
                imported = json.load(f)
            if not isinstance(imported, dict):
                raise ValueError("Invalid format.")
            added = updated = 0
            for k, v in imported.items():
                if k in data:
                    updated += 1
                else:
                    added += 1
                data[k] = v
            save_charging_points(data)
            callback()
            messagebox.showinfo("Import Complete", f"Added: {added}  |  Updated: {updated}")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    refresh_station_list()
    update_btn_states()