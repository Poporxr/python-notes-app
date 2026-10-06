"""Settings screen: note preferences and data options.

(Theme was intentionally left out — the app ships with one polished
dark-navy theme.)
"""

import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

from . import database as db
from .theme import COLORS, FONTS
from .widgets import ghost_button, primary_button, scrollable


def build_settings(content, app):
    tk.Label(content, text="Settings", bg=COLORS["bg"], fg=COLORS["text"],
             font=FONTS["display"]).pack(anchor="w", padx=24, pady=(20, 4))
    tk.Label(content, text="Tune the app to how you work.",
             bg=COLORS["bg"], fg=COLORS["muted"],
             font=FONTS["small"]).pack(anchor="w", padx=24, pady=(0, 12))

    scroll = scrollable(content)
    body = tk.Frame(scroll, bg=COLORS["bg"])
    body.pack(fill="x", padx=24, pady=(0, 24))

    # --- Note preferences -------------------------------------------------
    tk.Label(body, text="NOTE PREFERENCES", bg=COLORS["bg"],
             fg=COLORS["faint"], font=("Segoe UI", 9, "bold")).pack(
                 anchor="w", pady=(8, 10))

    card = tk.Frame(body, bg=COLORS["card"],
                    highlightbackground=COLORS["border"], highlightthickness=1)
    card.pack(fill="x", pady=(0, 16))

    # Your display name (used in the greeting).
    row = tk.Frame(card, bg=COLORS["card"])
    row.pack(fill="x", padx=16, pady=12)
    tk.Label(row, text="Your name", bg=COLORS["card"], fg=COLORS["text"],
             font=FONTS["body"]).pack(side="left")
    name_var = tk.StringVar(value=app.user_name)
    tk.Entry(row, textvariable=name_var, bg=COLORS["input"],
             fg=COLORS["text"], font=FONTS["body"],
             insertbackground=COLORS["text"], relief="flat",
             highlightbackground=COLORS["border"], highlightthickness=1,
             width=22).pack(side="right", ipady=4)

    # Autosave delay.
    row2 = tk.Frame(card, bg=COLORS["card"])
    row2.pack(fill="x", padx=16, pady=(0, 12))
    tk.Label(row2, text="Autosave after", bg=COLORS["card"],
             fg=COLORS["text"], font=FONTS["body"]).pack(side="left")
    delay_var = tk.StringVar(value=db.get_setting("autosave_ms", "1500"))
    tk.Entry(row2, textvariable=delay_var, bg=COLORS["input"],
             fg=COLORS["text"], font=FONTS["body"],
             insertbackground=COLORS["text"], relief="flat",
             highlightbackground=COLORS["border"], highlightthickness=1,
             width=8).pack(side="right", ipady=4)
    tk.Label(row2, text="ms of no typing", bg=COLORS["card"],
             fg=COLORS["muted"], font=FONTS["small"]).pack(side="right",
                                                           padx=(0, 8))

    def save_prefs():
        name = name_var.get().strip() or "Friend"
        try:
            delay = max(500, int(delay_var.get()))
        except ValueError:
            delay = 1500
        db.set_setting("user_name", name)
        db.set_setting("autosave_ms", str(delay))
        app.user_name = name
        app.autosave_ms = delay
        app.refresh_sidebar()
        messagebox.showinfo("Settings", "Preferences saved.")

    primary_button(body, "Save preferences", save_prefs).pack(anchor="w",
                                                              pady=(0, 24))

    # --- Data ---------------------------------------------------------------
    tk.Label(body, text="YOUR DATA", bg=COLORS["bg"], fg=COLORS["faint"],
             font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 10))

    card2 = tk.Frame(body, bg=COLORS["card"],
                     highlightbackground=COLORS["border"], highlightthickness=1)
    card2.pack(fill="x")
    tk.Label(card2, text="All notes live in a single SQLite file on this computer.",
             bg=COLORS["card"], fg=COLORS["muted"], font=FONTS["small"],
             wraplength=420, justify="left").pack(anchor="w", padx=16,
                                                  pady=(12, 4))
    tk.Label(card2, text=db.DB_PATH, bg=COLORS["card"], fg=COLORS["faint"],
             font=("Consolas", 8), wraplength=460, justify="left").pack(
                 anchor="w", padx=16, pady=(0, 12))

    btn_row = tk.Frame(body, bg=COLORS["bg"])
    btn_row.pack(fill="x", pady=12)

    def backup():
        dest = filedialog.asksaveasfilename(
            defaultextension=".db", initialfile="notes-backup.db",
            filetypes=[("SQLite database", "*.db")])
        if dest:
            shutil.copy2(db.DB_PATH, dest)
            messagebox.showinfo("Backup", "Backup saved.")

    ghost_button(btn_row, "Back up database", backup).pack(side="left")

    # --- About ----------------------------------------------------------------
    tk.Label(body, text="ABOUT", bg=COLORS["bg"], fg=COLORS["faint"],
             font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(16, 10))
    tk.Label(body, text="Notes — Capture. Organize. Create.\n"
                        "Built with Python, Tkinter, and SQLite.",
             bg=COLORS["bg"], fg=COLORS["muted"], font=FONTS["small"],
             justify="left").pack(anchor="w")
