"""
amount_screen.py

Do's:
    Builds the amount filter screen. Reads pending_context to
    determine the mode, station filter, and mapping choice, then
    calls run_etl with the correct parameters.

Dont's:
    - Any ETL logic
    - Any navigation logic (that's in app.py)
"""

import tkinter as tk


def build_amount_screen(frame, pending_context, nav, root, all_frames, run_etl):
    tk.Label(frame, text="Select Output", font=("Arial", 13, "bold")).pack(pady=(0, 12))

    def on_amount(f):
        use_mapping    = pending_context.get("use_mapping", False)
        station_filter = pending_context.get("station_filter", None)
        station_label  = pending_context.get("station_label", None)

        # Build the output label based on context
        label_base = station_label if station_filter else None

        if f == "both":
            run_etl(f"{label_base} - Paid"   if label_base else "Paid",
                    use_blacklist=True, station_filter=station_filter, amount_filter="paid",
                    use_mapping=use_mapping, root=root, frames=all_frames)
            run_etl(f"{label_base} - Unpaid" if label_base else "Unpaid",
                    use_blacklist=True, station_filter=station_filter, amount_filter="unpaid",
                    use_mapping=use_mapping, root=root, frames=all_frames)
        else:
            label = f"{label_base} - {'Paid' if f == 'paid' else 'Unpaid'}" if label_base else ("Paid" if f == "paid" else "Unpaid")
            run_etl(label, use_blacklist=True, station_filter=station_filter, amount_filter=f,
                    use_mapping=use_mapping, root=root, frames=all_frames)

    tk.Button(frame, text="Paid",        width=28, command=lambda: on_amount("paid")).pack(pady=4)
    tk.Button(frame, text="Unpaid",      width=28, command=lambda: on_amount("unpaid")).pack(pady=4)
    tk.Button(frame, text="Paid/Unpaid", width=28, command=lambda: on_amount("both")).pack(pady=4)
    tk.Frame(frame, height=1, bg="gray").pack(fill="x", pady=10)
    tk.Button(frame, text="← Back",     width=28, command=lambda: pending_context.get("back_from_amount", nav["show_main"])()).pack(pady=4)