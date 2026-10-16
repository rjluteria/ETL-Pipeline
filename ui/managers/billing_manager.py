"""
billing_manager.py

Do's:
    Opens the Manage Billing popup window. Handles adding and
    removing billing stations and billing customers/keywords.
    Supports import/export of billing config.

Dont's:
    - Any ETL logic
    - Any screen navigation
    - Any other manager logic
"""

import json
import tkinter as tk
from tkinter import filedialog, messagebox
from config.config_manager import get_billing, save_billing


def open_billing_manager():
    billing = get_billing()

    win = tk.Toplevel()
    win.title("Manage Billing")
    win.geometry("680x500")
    win.grab_set()

    # Left panel — billing stations
    left = tk.Frame(win)
    left.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)

    tk.Label(left, text="Billing Stations", font=("Arial", 10, "bold")).pack(anchor="w")

    station_list = tk.Listbox(left, width=32, height=18, exportselection=False)
    station_list.pack(fill="both", expand=True, pady=(4, 0))

    s_btn_row = tk.Frame(left)
    s_btn_row.pack(fill="x", pady=(6, 0))
    add_s_btn = tk.Button(s_btn_row, text="+ Add",  width=8)
    del_s_btn = tk.Button(s_btn_row, text="Remove", width=8)
    add_s_btn.pack(side="left")
    del_s_btn.pack(side="left", padx=4)

    # Right panel — billing customers
    right = tk.Frame(win)
    right.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=10)

    tk.Label(right, text="Billing Customers", font=("Arial", 10, "bold")).pack(anchor="w")
    tk.Label(right, text="(exact name or keyword — e.g. 'DHL')", font=("Arial", 8), fg="gray").pack(anchor="w")

    customer_list = tk.Listbox(right, width=32, height=18, exportselection=False)
    customer_list.pack(fill="both", expand=True, pady=(4, 0))

    c_btn_row = tk.Frame(right)
    c_btn_row.pack(fill="x", pady=(6, 0))
    add_c_btn = tk.Button(c_btn_row, text="+ Add",  width=8)
    del_c_btn = tk.Button(c_btn_row, text="Remove", width=8)
    add_c_btn.pack(side="left")
    del_c_btn.pack(side="left", padx=4)

    # Import / Export buttons
    ie_row = tk.Frame(win)
    ie_row.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
    tk.Button(ie_row, text="Export", width=12, command=lambda: export_billing(win, billing)).pack(side="left", padx=(0, 6))
    tk.Button(ie_row, text="Import", width=12, command=lambda: import_billing(win, billing, refresh_all)).pack(side="left")

    def refresh_all():
        # Rebuild both lists from current billing config
        station_list.delete(0, tk.END)
        for s in billing.get("stations", []):
            station_list.insert(tk.END, s)
        customer_list.delete(0, tk.END)
        for c in billing.get("customers", []):
            customer_list.insert(tk.END, c)
        update_btn_states()

    def update_btn_states():
        del_s_btn.config(state="normal" if station_list.curselection() else "disabled")
        del_c_btn.config(state="normal" if customer_list.curselection() else "disabled")

    station_list.bind("<<ListboxSelect>>",  lambda e: update_btn_states())
    customer_list.bind("<<ListboxSelect>>", lambda e: update_btn_states())

    def on_add_station():
        form = tk.Toplevel(win)
        form.title("Add Station")
        form.geometry("340x110")
        form.grab_set()
        form.resizable(False, False)
        tk.Label(form, text="Station Name:").grid(row=0, column=0, sticky="w", padx=16, pady=12)
        entry = tk.Entry(form, width=28)
        entry.grid(row=0, column=1, pady=12)
        def save():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Missing", "Please enter a station name.", parent=form)
                return
            if name in billing["stations"]:
                messagebox.showwarning("Duplicate", f"'{name}' already exists.", parent=form)
                return
            billing["stations"].append(name)
            save_billing(billing)
            refresh_all()
            form.destroy()
        tk.Button(form, text="Save", width=10, command=save).grid(row=1, column=0, columnspan=2, pady=8)

    def on_del_station():
        sel = station_list.curselection()
        if not sel:
            return
        name = station_list.get(sel[0])
        if messagebox.askyesno("Remove", f"Remove '{name}' from billing stations?"):
            billing["stations"] = [s for s in billing["stations"] if s != name]
            save_billing(billing)
            refresh_all()

    def on_add_customer():
        form = tk.Toplevel(win)
        form.title("Add Customer")
        form.geometry("340x110")
        form.grab_set()
        form.resizable(False, False)
        tk.Label(form, text="Name / Keyword:").grid(row=0, column=0, sticky="w", padx=16, pady=12)
        entry = tk.Entry(form, width=28)
        entry.grid(row=0, column=1, pady=12)
        def save():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Missing", "Please enter a name or keyword.", parent=form)
                return
            if name in billing["customers"]:
                messagebox.showwarning("Duplicate", f"'{name}' already exists.", parent=form)
                return
            billing["customers"].append(name)
            save_billing(billing)
            refresh_all()
            form.destroy()
        tk.Button(form, text="Save", width=10, command=save).grid(row=1, column=0, columnspan=2, pady=8)

    def on_del_customer():
        sel = customer_list.curselection()
        if not sel:
            return
        name = customer_list.get(sel[0])
        if messagebox.askyesno("Remove", f"Remove '{name}' from billing customers?"):
            billing["customers"] = [c for c in billing["customers"] if c != name]
            save_billing(billing)
            refresh_all()

    def export_billing(parent, b):
        dest = filedialog.asksaveasfilename(
            parent=parent, defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="billing.json", title="Export Billing Config"
        )
        if not dest:
            return
        try:
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(b, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Export Complete", f"Exported to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def import_billing(parent, b, callback):
        src = filedialog.askopenfilename(
            parent=parent, filetypes=[("JSON files", "*.json")], title="Import Billing Config"
        )
        if not src:
            return
        try:
            with open(src, "r", encoding="utf-8") as f:
                imported = json.load(f)
            if not isinstance(imported, dict):
                raise ValueError("Invalid format.")
            b.update(imported)
            save_billing(b)
            callback()
            messagebox.showinfo("Import Complete", "Billing config imported.")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    add_s_btn.config(command=on_add_station)
    del_s_btn.config(command=on_del_station)
    add_c_btn.config(command=on_add_customer)
    del_c_btn.config(command=on_del_customer)

    refresh_all()
    update_btn_states()