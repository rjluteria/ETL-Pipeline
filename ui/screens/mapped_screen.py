"""
mapped_screen.py

Do's:
    Builds the Mapped/Unmapped selection screen. Stores the user's
    choice in pending_context and navigates to the amount screen.

Dont's:
    - Any ETL logic
    - Any navigation logic (that's in app.py)
"""

import tkinter as tk


def build_mapped_screen(frame, pending_context, nav):
    tk.Label(frame, text="Output Type", font=("Arial", 13, "bold")).pack(pady=(0, 12))

    def on_mapped(mapped):
        # Store mapping choice and move to amount screen
        pending_context["use_mapping"] = mapped
        nav["show_amount"](lambda: nav["show_mapped"](pending_context.get("back_from_mapped", nav["show_main"])))

    tk.Button(frame, text="Mapped",   width=28, command=lambda: on_mapped(True)).pack(pady=4)
    tk.Button(frame, text="Unmapped", width=28, command=lambda: on_mapped(False)).pack(pady=4)
    tk.Frame(frame, height=1, bg="gray").pack(fill="x", pady=10)
    tk.Button(frame, text="← Back",  width=28, command=lambda: pending_context.get("back_from_mapped", nav["show_main"])()).pack(pady=4)