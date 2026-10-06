"""The All Notes / Pinned / Favorites / Archive screens.

One builder handles all four; only the query and the headings change.
Cards support click-to-select so the Delete key works on lists too.
"""

import tkinter as tk

from . import database as db
from .theme import COLORS, FONTS, TAG_COLORS
from .widgets import note_card, empty_state, primary_button, scrollable

TITLES = {
    "all": ("All Notes", "Every note that isn't archived."),
    "pinned": ("Pinned", "Notes you pinned for quick access."),
    "favorites": ("Favorites", "Notes you marked with a star."),
    "archive": ("Archive", "Archived notes. Restore them or delete forever."),
}

EMPTY = {
    "all": ("No notes yet", "Click New Note to write your first one."),
    "pinned": ("Nothing pinned", "Pin a note from its menu to see it here."),
    "favorites": ("No favorites", "Star a note from its menu to see it here."),
    "archive": ("Archive is empty", "Archived notes will show up here."),
}


def build_notes_list(content, app, mode="all"):
    title, hint = TITLES[mode]
    app.selected_note_id = None  # selection never survives a screen switch

    header = tk.Frame(content, bg=COLORS["bg"])
    header.pack(fill="x", padx=24, pady=(20, 4))
    tk.Label(header, text=title, bg=COLORS["bg"], fg=COLORS["text"],
             font=FONTS["display"]).pack(side="left")
    if mode != "archive":
        primary_button(header, "+  New Note",
                       lambda: app.show("editor")).pack(side="right")
    tk.Label(content, text=hint, bg=COLORS["bg"], fg=COLORS["muted"],
             font=FONTS["small"]).pack(anchor="w", padx=24, pady=(0, 12))

    notes = db.list_notes(mode=mode)
    if not notes:
        icon, msg = EMPTY[mode][0], EMPTY[mode][1]
        empty_state(content, "\u25a4", icon, msg)
        return

    scroll = scrollable(content)
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
