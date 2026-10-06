"""The Home dashboard: greeting, stat tiles, and recent notes."""

import tkinter as tk
from datetime import datetime

from . import database as db
from .theme import COLORS, FONTS, ICONS, TAG_COLORS
from .widgets import stat_card, note_card, empty_state, primary_button, scrollable


def greeting():
    """Time-aware greeting like the reference design."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def build_home(content, app):
    scroll = scrollable(content)

    # Greeting -----------------------------------------------------------
    tk.Label(scroll, text=f"{greeting()}, {app.user_name}",
             bg=COLORS["bg"], fg=COLORS["text"],
             font=FONTS["display"]).pack(anchor="w", padx=24, pady=(20, 2))
    tk.Label(scroll, text="Here's what's happening with your notes today.",
             bg=COLORS["bg"], fg=COLORS["muted"],
             font=FONTS["body"]).pack(anchor="w", padx=24)

    # Stat tiles ----------------------------------------------------------
    total = db.count_notes()
    folders = len(db.list_folders())
    pinned = db.count_notes("archived = 0 AND pinned = 1")
    favorites = db.count_notes("archived = 0 AND favorite = 1")

    stats = tk.Frame(scroll, bg=COLORS["bg"])
    stats.pack(fill="x", padx=24, pady=(18, 0))
    for i in range(4):
        stats.columnconfigure(i, weight=1, uniform="stat")

    tiles = [
        (ICONS["notes"], COLORS["accent"], total, "Total Notes",
         lambda: app.show("notes", mode="all")),
        (ICONS["folder"], COLORS["green"], folders, "Folders",
         lambda: app.show("folders")),
        (ICONS["pin"], COLORS["purple"], pinned, "Pinned Notes",
         lambda: app.show("notes", mode="pinned")),
        (ICONS["star"], COLORS["amber"], favorites, "Favorites",
         lambda: app.show("notes", mode="favorites")),
    ]
    for i, (icon, color, number, label, cmd) in enumerate(tiles):
        tile = stat_card(stats, icon, color, number, label, command=cmd)
        tile.grid(row=0, column=i, sticky="ew", padx=(0, 12) if i < 3 else 0)

    # Recent notes header -------------------------------------------------
    header = tk.Frame(scroll, bg=COLORS["bg"])
    header.pack(fill="x", padx=24, pady=(26, 12))
    tk.Label(header, text="Recent Notes", bg=COLORS["bg"], fg=COLORS["text"],
             font=FONTS["title"]).pack(side="left")
    new_btn = primary_button(header, f"{ICONS['plus']}  New Note",
                             lambda: app.show("editor"))
    new_btn.pack(side="right")

    # Note grid ------------------------------------------------------------
    notes = db.list_notes()[:6]
    if not notes:
        empty_state(scroll, ICONS["notes"], "No notes yet",
                    "Click New Note to write your first one.")
        return

    grid = tk.Frame(scroll, bg=COLORS["bg"])
    grid.pack(fill="x", padx=24, pady=(0, 24))
    grid.columnconfigure(0, weight=1, uniform="note")
    grid.columnconfigure(1, weight=1, uniform="note")

    for i, note in enumerate(notes):
        tags = db.get_note_tags(note["id"])
        color = TAG_COLORS[i % len(TAG_COLORS)]
        card = note_card(grid, note, tags, color,
                         on_open=lambda nid: app.show("editor", note_id=nid),
                         on_menu=lambda e, n=note: app.note_menu(e, n))
        card.grid(row=i // 2, column=i % 2, sticky="ew",
                  padx=(0, 12) if i % 2 == 0 else 0, pady=(0, 12))
