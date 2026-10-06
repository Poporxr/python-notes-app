"""Folders, tags, and search screens."""

import tkinter as tk

from . import database as db
from .theme import COLORS, FONTS, ICONS, FOLDER_COLORS, TAG_COLORS
from .widgets import (note_card, empty_state, primary_button, scrollable,
                      confirm_dialog, input_dialog)


# --------------------------------------------------------------- folders ---

def build_folders(content, app):
    header = tk.Frame(content, bg=COLORS["bg"])
    header.pack(fill="x", padx=24, pady=(20, 12))
    tk.Label(header, text="Folders", bg=COLORS["bg"], fg=COLORS["text"],
             font=FONTS["display"]).pack(side="left")
    primary_button(header, f"{ICONS['plus']}  New Folder",
                   lambda: new_folder(content, app)).pack(side="right")

    folders = db.list_folders()
    if not folders:
        empty_state(content, ICONS["folder"], "No folders yet",
                    "Create one to start organizing your notes.")
        return

    scroll = scrollable(content)
    for i, folder in enumerate(folders):
        color = FOLDER_COLORS[i % len(FOLDER_COLORS)]
        row = tk.Frame(scroll, bg=COLORS["card"],
                       highlightbackground=COLORS["border"],
                       highlightthickness=1, cursor="hand2")
        row.pack(fill="x", padx=24, pady=(0, 10))

        badge = tk.Frame(row, bg=color, width=36, height=36)
        badge.pack(side="left", padx=12, pady=12)
        badge.pack_propagate(False)
        tk.Label(badge, text=ICONS["folder"], bg=color, fg="white",
                 font=("Segoe UI", 15)).pack(expand=True)

        tk.Label(row, text=folder["name"], bg=COLORS["card"],
                 fg=COLORS["text"], font=FONTS["body"]).pack(side="left")
        tk.Label(row, text=f"{folder['note_count']} notes", bg=COLORS["card"],
                 fg=COLORS["faint"], font=FONTS["small"]).pack(
                     side="left", padx=(10, 0))

        menu = tk.Label(row, text=ICONS["dots"], bg=COLORS["card"],
                        fg=COLORS["muted"], font=("Segoe UI", 12), cursor="hand2")
        menu.pack(side="right", padx=12)
        menu.bind("<Button-1>", lambda e, f=folder: folder_menu(e, f, content, app))

        row.bind("<Button-1>",
                 lambda _e, fid=folder["id"]: app.show("folder", folder_id=fid))


def folder_menu(event, folder, content, app):
    menu = tk.Menu(content, tearoff=0, bg=COLORS["card"], fg=COLORS["text"],
                   activebackground=COLORS["accent"])
    menu.add_command(label="Open",
                     command=lambda: app.show("folder", folder_id=folder["id"]))
    menu.add_command(label="Rename",
                     command=lambda: rename_folder(content, app, folder))
    menu.add_command(label="Delete",
                     command=lambda: remove_folder(content, app, folder))
    menu.tk_popup(event.x_root, event.y_root)


def new_folder(content, app):
    name = input_dialog(content, "New folder", "Folder name:")
    if name:
        try:
            db.create_folder(name)
        except Exception:
            # Name already exists; just refresh.
            pass
        app.refresh_sidebar()
        app.show("folders")


def rename_folder(content, app, folder):
    name = input_dialog(content, "Rename folder", "New name:",
                        initial=folder["name"])
    if name:
        db.rename_folder(folder["id"], name)
        app.refresh_sidebar()
        app.show("folders")


def remove_folder(content, app, folder):
    if confirm_dialog(content, "Delete folder",
                       f'Delete "{folder["name"]}"? Its notes become unfiled.'):
        db.delete_folder(folder["id"])
        app.refresh_sidebar()
        app.show("folders")


def build_folder_detail(content, app, folder_id):
    folder = db.get_folder(folder_id)
    if not folder:
        app.show("folders")
        return

    header = tk.Frame(content, bg=COLORS["bg"])
    header.pack(fill="x", padx=24, pady=(20, 4))
    back = tk.Label(header, text=f"{ICONS['back']}  Folders", bg=COLORS["bg"],
                    fg=COLORS["muted"], font=FONTS["body"], cursor="hand2")
    back.pack(side="left")
    back.bind("<Button-1>", lambda _e: app.show("folders"))
    tk.Label(content, text=folder["name"], bg=COLORS["bg"], fg=COLORS["text"],
             font=FONTS["display"]).pack(anchor="w", padx=24, pady=(8, 12))

    notes = db.list_notes(folder_id=folder_id)
    if not notes:
        empty_state(content, ICONS["notes"], "Folder is empty",
                    "New notes filed here will show up in this folder.")
        return

    scroll = scrollable(content)
    grid = tk.Frame(scroll, bg=COLORS["bg"])
    grid.pack(fill="x", padx=24, pady=(0, 24))
    grid.columnconfigure(0, weight=1, uniform="note")
    grid.columnconfigure(1, weight=1, uniform="note")
    for i, note in enumerate(notes):
        tags = db.get_note_tags(note["id"])
        card = note_card(grid, note, tags, TAG_COLORS[i % len(TAG_COLORS)],
                         on_open=lambda nid: app.show("editor", note_id=nid),
                         on_menu=lambda e, n=note: app.note_menu(e, n))
        card.grid(row=i // 2, column=i % 2, sticky="ew",
                  padx=(0, 12) if i % 2 == 0 else 0, pady=(0, 12))


# ------------------------------------------------------------------ tags ---

def build_tags(content, app):
    tk.Label(content, text="Tags", bg=COLORS["bg"], fg=COLORS["text"],
             font=FONTS["display"]).pack(anchor="w", padx=24, pady=(20, 4))
    tk.Label(content, text="Browse every tag and the notes behind it.",
             bg=COLORS["bg"], fg=COLORS["muted"],
             font=FONTS["small"]).pack(anchor="w", padx=24, pady=(0, 12))

    tags = db.list_tags()
    if not tags:
        empty_state(content, ICONS["tag_dot"], "No tags yet",
                    "Add tags to a note in the editor, separated by commas.")
        return

    scroll = scrollable(content)
    wrap = tk.Frame(scroll, bg=COLORS["bg"])
    wrap.pack(fill="x", padx=24, pady=(0, 24))

    # Flow the tag pills left to right like the reference design.
    row = tk.Frame(wrap, bg=COLORS["bg"])
    row.pack(fill="x")
    for i, tag in enumerate(tags):
        color = TAG_COLORS[i % len(TAG_COLORS)]
        pill = tk.Frame(row, bg=COLORS["card"],
                        highlightbackground=color, highlightthickness=1,
                        cursor="hand2")
        pill.pack(side="left", padx=(0, 10), pady=(0, 10))
        tk.Label(pill, text=f"{ICONS['tag_dot']} #{tag['name']}",
                 bg=COLORS["card"], fg=color, font=FONTS["body"],
                 padx=12, pady=8).pack(side="left")
        tk.Label(pill, text=str(tag["note_count"]), bg=COLORS["card"],
                 fg=COLORS["faint"], font=FONTS["small"]).pack(side="left",
                                                               padx=(0, 12))

        pill.bind("<Button-1>",
                  lambda _e, tid=tag["id"]: app.show("tag", tag_id=tid))
        for child in pill.winfo_children():
            child.bind("<Button-1>",
                       lambda _e, tid=tag["id"]: app.show("tag", tag_id=tid))


def build_tag_detail(content, app, tag_id):
    tag = db.get_tag(tag_id)
    if not tag:
        app.show("tags")
        return

    header = tk.Frame(content, bg=COLORS["bg"])
    header.pack(fill="x", padx=24, pady=(20, 4))
    back = tk.Label(header, text=f"{ICONS['back']}  Tags", bg=COLORS["bg"],
                    fg=COLORS["muted"], font=FONTS["body"], cursor="hand2")
    back.pack(side="left")
    back.bind("<Button-1>", lambda _e: app.show("tags"))
    tk.Label(content, text=f"#{tag['name']}", bg=COLORS["bg"],
             fg=COLORS["text"], font=FONTS["display"]).pack(
                 anchor="w", padx=24, pady=(8, 12))

    notes = db.list_notes(tag_id=tag_id)
    if not notes:
        empty_state(content, ICONS["notes"], "No notes with this tag",
                    "Tag a note in the editor to see it here.")
        return

    scroll = scrollable(content)
    grid = tk.Frame(scroll, bg=COLORS["bg"])
    grid.pack(fill="x", padx=24, pady=(0, 24))
    grid.columnconfigure(0, weight=1, uniform="note")
    grid.columnconfigure(1, weight=1, uniform="note")
    for i, note in enumerate(notes):
        tags = db.get_note_tags(note["id"])
        card = note_card(grid, note, tags, TAG_COLORS[i % len(TAG_COLORS)],
                         on_open=lambda nid: app.show("editor", note_id=nid),
                         on_menu=lambda e, n=note: app.note_menu(e, n))
        card.grid(row=i // 2, column=i % 2, sticky="ew",
                  padx=(0, 12) if i % 2 == 0 else 0, pady=(0, 12))


# ---------------------------------------------------------------- search ---

def build_search(content, app, query):
    tk.Label(content, text=f'Results for "{query}"', bg=COLORS["bg"],
             fg=COLORS["text"], font=FONTS["display"]).pack(
                 anchor="w", padx=24, pady=(20, 4))
    results = db.search_notes(query)
    tk.Label(content, text=f"{len(results)} note(s) found in titles, "
                            "content, and tags.",
             bg=COLORS["bg"], fg=COLORS["muted"],
             font=FONTS["small"]).pack(anchor="w", padx=24, pady=(0, 12))

    if not results:
        empty_state(content, ICONS["search"], "Nothing found",
                    f'No notes match "{query}". Try different words.')
        return

    scroll = scrollable(content)
    grid = tk.Frame(scroll, bg=COLORS["bg"])
    grid.pack(fill="x", padx=24, pady=(0, 24))
    grid.columnconfigure(0, weight=1, uniform="note")
    grid.columnconfigure(1, weight=1, uniform="note")
    for i, note in enumerate(results):
        tags = db.get_note_tags(note["id"])
        card = note_card(grid, note, tags, TAG_COLORS[i % len(TAG_COLORS)],
                         on_open=lambda nid: app.show("editor", note_id=nid),
                         on_menu=lambda e, n=note: app.note_menu(e, n))
        card.grid(row=i // 2, column=i % 2, sticky="ew",
                  padx=(0, 12) if i % 2 == 0 else 0, pady=(0, 12))
