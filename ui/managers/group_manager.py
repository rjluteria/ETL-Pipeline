"""
group_manager.py

Do's:
    Opens the Manage Groups popup window. Handles adding, editing,
    and deleting groups and their members. Supports import/export.

Dont's:
    - Any ETL logic
    - Any screen navigation
    - Any other manager logic
"""

import json
import tkinter as tk
from tkinter import filedialog, messagebox
from config.config_manager import get_groups, save_groups


def open_group_manager(on_close_callback=None):
    groups = get_groups()

    win = tk.Toplevel()
    win.title("Manage Groups")
    win.geometry("680x520")
    win.grab_set()

    if on_close_callback:
        win.protocol("WM_DELETE_WINDOW", lambda: [on_close_callback(), win.destroy()])

    # Left panel — group list
    left = tk.Frame(win, width=220)
    left.pack(side="left", fill="y", padx=(10, 0), pady=10)

    tk.Label(left, text="Groups", font=("Arial", 10, "bold")).pack(anchor="w")

    group_list = tk.Listbox(left, width=26, height=20, exportselection=False)
    group_list.pack(fill="y", expand=True, pady=(4, 0))

    group_btn_row = tk.Frame(left)
    group_btn_row.pack(fill="x", pady=(6, 0))
    add_group_btn  = tk.Button(group_btn_row, text="+ Add",  width=8)
    edit_group_btn = tk.Button(group_btn_row, text="Edit",   width=8)
    del_group_btn  = tk.Button(group_btn_row, text="Delete", width=8)
    add_group_btn.pack(side="left")
    edit_group_btn.pack(side="left", padx=2)
    del_group_btn.pack(side="left")

    # Right panel — members list
    right = tk.Frame(win)
    right.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    tk.Label(right, text="Members", font=("Arial", 10, "bold")).pack(anchor="w")

    member_list = tk.Listbox(right, width=36, height=20, exportselection=False)
    member_list.pack(fill="both", expand=True, pady=(4, 0))

    member_btn_row = tk.Frame(right)
    member_btn_row.pack(fill="x", pady=(6, 0))
    add_member_btn = tk.Button(member_btn_row, text="+ Add Member",  width=14)
    del_member_btn = tk.Button(member_btn_row, text="Remove Member", width=14)
    add_member_btn.pack(side="left")
    del_member_btn.pack(side="left", padx=6)

    # Import / Export buttons
    ie_row = tk.Frame(win)
    ie_row.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
    tk.Button(ie_row, text="Import Groups", width=14, command=lambda: import_groups(win, groups, refresh_all)).pack(side="left", padx=(0, 6))
    tk.Button(ie_row, text="Export Groups", width=14, command=lambda: export_groups(win, groups)).pack(side="left")

    def refresh_group_list():
        group_list.delete(0, tk.END)
        for g in groups:
            group_list.insert(tk.END, g)
        refresh_member_list()
        update_btn_states()

    def refresh_member_list():
        member_list.delete(0, tk.END)
        sel = group_list.curselection()
        if sel:
            group_name = group_list.get(sel[0])
            for m in groups.get(group_name, []):
                member_list.insert(tk.END, m)
        update_btn_states()

    def update_btn_states():
        group_selected  = bool(group_list.curselection())
        member_selected = bool(member_list.curselection())
        edit_group_btn.config(state="normal" if group_selected else "disabled")
        del_group_btn.config(state="normal"  if group_selected else "disabled")
        add_member_btn.config(state="normal" if group_selected else "disabled")
        del_member_btn.config(state="normal" if (group_selected and member_selected) else "disabled")

    group_list.bind("<<ListboxSelect>>",  lambda e: refresh_member_list())
    member_list.bind("<<ListboxSelect>>", lambda e: update_btn_states())

    def refresh_all():
        refresh_group_list()

    def on_add_group():
        form = tk.Toplevel(win)
        form.title("Add Group")
        form.geometry("320x120")
        form.grab_set()
        form.resizable(False, False)
        tk.Label(form, text="Group Name:").grid(row=0, column=0, padx=16, pady=16, sticky="w")
        name_entry = tk.Entry(form, width=24)
        name_entry.grid(row=0, column=1, pady=16)
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Missing Info", "Please enter a group name.", parent=form)
                return
            if name in groups:
                messagebox.showwarning("Duplicate", f"Group '{name}' already exists.", parent=form)
                return
            groups[name] = []
            save_groups(groups)
            refresh_group_list()
            form.destroy()
        tk.Button(form, text="Save", width=10, command=save).grid(row=1, column=0, columnspan=2, pady=8)

    def on_edit_group():
        sel = group_list.curselection()
        if not sel:
            return
        old_name = group_list.get(sel[0])
        form = tk.Toplevel(win)
        form.title("Edit Group Name")
        form.geometry("320x120")
        form.grab_set()
        form.resizable(False, False)
        tk.Label(form, text="Group Name:").grid(row=0, column=0, padx=16, pady=16, sticky="w")
        name_entry = tk.Entry(form, width=24)
        name_entry.insert(0, old_name)
        name_entry.grid(row=0, column=1, pady=16)
        def save():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("Missing Info", "Please enter a group name.", parent=form)
                return
            if new_name != old_name and new_name in groups:
                messagebox.showwarning("Duplicate", f"Group '{new_name}' already exists.", parent=form)
                return
            groups[new_name] = groups.pop(old_name)
            save_groups(groups)
            refresh_group_list()
            form.destroy()
        tk.Button(form, text="Save", width=10, command=save).grid(row=1, column=0, columnspan=2, pady=8)

    def on_delete_group():
        sel = group_list.curselection()
        if not sel:
            return
        name = group_list.get(sel[0])
        if messagebox.askyesno("Delete Group", f"Delete group '{name}' and all its members?"):
            groups.pop(name, None)
            save_groups(groups)
            refresh_group_list()

    def normalize_member(name):
        # Normalize to "Last, First" lowercase for duplicate checking
        name = str(name).strip().lower()
        parts = name.split(",", 1)
        if len(parts) == 2:
            return parts[0].strip() + ", " + parts[1].strip()
        return name

    def on_add_member():
        sel = group_list.curselection()
        if not sel:
            return
        group_name = group_list.get(sel[0])
        form = tk.Toplevel(win)
        form.title("Add Member")
        form.geometry("360x120")
        form.grab_set()
        form.resizable(False, False)
        tk.Label(form, text="Member Name:").grid(row=0, column=0, padx=16, pady=16, sticky="w")
        name_entry = tk.Entry(form, width=28)
        name_entry.grid(row=0, column=1, pady=16)
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Missing Info", "Please enter a member name.", parent=form)
                return
            normalized_new = normalize_member(name)
            # Check for duplicates across all groups
            for grp, members in groups.items():
                for member in members:
                    if normalize_member(member) == normalized_new:
                        msg = f"'{name}' already exists in group '{grp}' as '{member}'.\n\nDo you still want to add them?"
                        if not messagebox.askyesno("Duplicate Found", msg, parent=form):
                            return
                        break
            groups[group_name].append(name)
            save_groups(groups)
            refresh_member_list()
            form.destroy()
        tk.Button(form, text="Save", width=10, command=save).grid(row=1, column=0, columnspan=2, pady=8)

    def on_remove_member():
        group_sel  = group_list.curselection()
        member_sel = member_list.curselection()
        if not group_sel or not member_sel:
            return
        group_name  = group_list.get(group_sel[0])
        member_name = member_list.get(member_sel[0])
        if messagebox.askyesno("Remove Member", f"Remove '{member_name}' from '{group_name}'?"):
            groups[group_name].remove(member_name)
            save_groups(groups)
            refresh_member_list()

    def export_groups(parent, grps):
        dest = filedialog.asksaveasfilename(
            parent=parent, defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="usergroups.json", title="Export Groups"
        )
        if not dest:
            return
        try:
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(grps, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Export Complete", f"Groups exported to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def import_groups(parent, grps, callback):
        src = filedialog.askopenfilename(
            parent=parent, filetypes=[("JSON files", "*.json")], title="Import Groups"
        )
        if not src:
            return
        try:
            with open(src, "r", encoding="utf-8") as f:
                imported = json.load(f)
            if not isinstance(imported, dict):
                raise ValueError("Invalid groups file format.")
            added = updated = 0
            for k, v in imported.items():
                if k in grps:
                    updated += 1
                else:
                    added += 1
                grps[k] = v
            save_groups(grps)
            callback()
            messagebox.showinfo("Import Complete", f"Import successful.\nAdded: {added}  |  Updated: {updated}")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    add_group_btn.config(command=on_add_group)
    edit_group_btn.config(command=on_edit_group)
    del_group_btn.config(command=on_delete_group)
    add_member_btn.config(command=on_add_member)
    del_member_btn.config(command=on_remove_member)

    refresh_group_list()
    update_btn_states()