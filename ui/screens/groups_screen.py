"""
groups_screen.py

Do's:
    Builds the User Groups screen. Shows a button for each group
    that triggers an ETL run for that group's members.

Dont's:
    - Any ETL logic
    - Any group management (that's in managers/group_manager.py)
    - Any navigation logic (that's in app.py)
"""

import tkinter as tk
from config.config_manager import get_groups


def build_groups_screen(frame, pending_context, nav, root, all_frames, run_etl):
    tk.Label(frame, text="User Groups", font=("Arial", 13, "bold")).pack(pady=(0, 8))

    # Container for dynamically generated group buttons
    group_btn_frame = tk.Frame(frame)
    group_btn_frame.pack()

    tk.Frame(frame, height=1, bg="gray").pack(fill="x", pady=10)
    tk.Button(frame, text="← Back", width=28, command=nav["show_main"]).pack(pady=4)

    def refresh_group_buttons():
        # Clear and rebuild group buttons from current config
        for widget in group_btn_frame.winfo_children():
            widget.destroy()
        groups = get_groups()
        for label, members in groups.items():
            tk.Button(
                group_btn_frame, text=label, width=28,
                command=lambda l=label, n=set(members): run_etl(
                    l, n, use_blacklist=False, use_mapping=False, root=root, frames=all_frames
                )
            ).pack(pady=3)

    # Return refresh function so app.py can call it when navigating to this screen
    return refresh_group_buttons