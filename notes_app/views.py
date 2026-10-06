"""All screens. The core pattern is master-detail: a note list on the
left, the editor on the right. One reusable layout, used by every
list screen (All Notes, Pinned, Favorites, Archive, folders, search).
"""

import tkinter as tk
from datetime import datetime

from . import database as db
from .theme import COLORS, FONTS
from .widgets import (clear, empty_state, primary_button, text_button,
                      confirm_dialog, input_dialog, scrollable,
                      relative_time)


# ------------------------------------------------------- note list row ---

def snippet_of(note, length=60):
    """First line of the body, shortened for the list."""
    text = (note["body"] or "").replace("\n", " ").strip()
    return text[:length] + "..." if len(text) > length else text


class NoteList(tk.Frame):
    """Left panel: clickable rows of title + snippet + date."""

    def __init__(self, parent, on_select):
        super().__init__(parent, bg=COLORS["bg"])
        self.on_select = on_select
        self.rows = {}  # note_id -> row frame
        self.selected_id = None

    def show(self, notes):
        clear(self)
        self.rows = {}
        for note in notes:
            self.add_row(note)
        # Keep the selection if that note is still in the list.
        if self.selected_id in self.rows:
            self.highlight(self.selected_id)

    def add_row(self, note):
        row = tk.Frame(self, bg=COLORS["card"],
                       highlightbackground=COLORS["border"],
                       highlightthickness=1, cursor="hand2")
        row.pack(fill="x", pady=(0, 8))

        title = note["title"] or "Untitled"
        if note["pinned"]:
            title += "  ·  PINNED"
        tk.Label(row, text=title, bg=COLORS["card"], fg=COLORS["text"],
                 font=FONTS["title"], anchor="w").pack(
                     fill="x", padx=12, pady=(10, 0))
        snip = snippet_of(note)
        if snip:
            tk.Label(row, text=snip, bg=COLORS["card"], fg=COLORS["muted"],
                     font=FONTS["small"], anchor="w").pack(
                         fill="x", padx=12)
        tk.Label(row, text=relative_time(note["updated"]),
                 bg=COLORS["card"], fg=COLORS["faint"],
                 font=FONTS["tiny"], anchor="w").pack(
                     fill="x", padx=12, pady=(2, 10))

        nid = note["id"]
        row.bind("<Button-1>", lambda _e: self.select(nid))
        for child in row.winfo_children():
            child.bind("<Button-1>", lambda _e: self.select(nid))
        self.rows[nid] = row

    def select(self, note_id):
        self.highlight(note_id)
        self.on_select(note_id)

    def highlight(self, note_id):
        self.selected_id = note_id
        for nid, row in self.rows.items():
            bg = COLORS["selected"] if nid == note_id else COLORS["card"]
            row.configure(bg=bg)
            for child in row.winfo_children():
                try:
                    child.configure(bg=bg)
                except tk.TclError:
                    pass


# ---------------------------------------------------------- editor panel ---

class EditorPanel(tk.Frame):
    """Right panel: the note itself. Title up top, body below."""

    def __init__(self, parent, app, on_change):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.on_change = on_change  # called after any save/delete
        self.note_id = None
        self.note = None
        self._timer = None
        self._build_empty()

    # -- layout ---------------------------------------------------------

    def _build_empty(self):
        clear(self)
        box = tk.Frame(self, bg=COLORS["bg"])
        box.pack(expand=True)
        tk.Label(box, text="Select a note on the left,",
                 bg=COLORS["bg"], fg=COLORS["muted"],
                 font=FONTS["body"]).pack()
        tk.Label(box, text="or create a new one.",
                 bg=COLORS["bg"], fg=COLORS["muted"],
                 font=FONTS["body"]).pack()

    def _build_editor(self):
        clear(self)
        note = self.note

        # Top bar: folder, flags, saved indicator -------------------------
        bar = tk.Frame(self, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(0, 8))

        folders = db.list_folders()
        names = ["No folder"] + [f["name"] for f in folders]
        current = next((f["name"] for f in folders
                        if f["id"] == note["folder_id"]), "No folder")
        self.folder_var = tk.StringVar(value=current)
        menu = tk.OptionMenu(bar, self.folder_var, *names)
        menu.configure(bg=COLORS["card"], fg=COLORS["muted"],
                       font=FONTS["small"], relief="flat",
                       highlightbackground=COLORS["border"],
                       highlightthickness=1, padx=8)
        menu["menu"].configure(bg=COLORS["card"], fg=COLORS["text"])
        menu.pack(side="left")
        self.folder_var.trace_add("write", lambda *_: self.schedule())

        self.saved_lbl = tk.Label(bar, text="", bg=COLORS["bg"],
                                  fg=COLORS["green"], font=FONTS["small"])
        self.saved_lbl.pack(side="right")

        # Pin / Favorite / Archive toggles as plain text buttons ----------
        self.pin_btn = text_button(
            bar, "", lambda: self.toggle("pinned"), COLORS["amber"])
        self.pin_btn.pack(side="right", padx=6)
        self.fav_btn = text_button(
            bar, "", lambda: self.toggle("favorite"), COLORS["amber"])
        self.fav_btn.pack(side="right", padx=6)
        if note["archived"]:
            text_button(bar, "Restore",
                        self.restore, COLORS["green"]).pack(side="right",
                                                           padx=6)
        else:
            self.arc_btn = text_button(bar, "Archive",
                                       lambda: self.toggle("archived"))
            self.arc_btn.pack(side="right", padx=6)
        self.refresh_toggles()

        # Title: the head/topic of the note, big and prominent -------------
        self.title_var = tk.StringVar(value=note["title"])
        title = tk.Entry(self, textvariable=self.title_var, bg=COLORS["bg"],
                         fg=COLORS["text"], font=FONTS["display"],
                         insertbackground=COLORS["text"], relief="flat",
                         highlightthickness=0, bd=0)
        title.pack(fill="x", pady=(4, 8))
        title.bind("<KeyRelease>", lambda _e: self.schedule())
        self.title_entry = title

        # Body --------------------------------------------------------------
        frame = tk.Frame(self, bg=COLORS["card"],
                         highlightbackground=COLORS["border"],
                         highlightthickness=1)
        frame.pack(fill="both", expand=True)
        self.body = tk.Text(frame, bg=COLORS["card"], fg=COLORS["text"],
                            font=("Segoe UI", 11),
                            insertbackground=COLORS["text"],
                            relief="flat", highlightthickness=0, bd=0,
                            wrap="word", padx=14, pady=14, undo=True)
        self.body.pack(fill="both", expand=True)
        self.body.insert("1.0", note["body"] or "")
        self.body.bind("<KeyRelease>", lambda _e: self.schedule())

        # Bottom: word count, timestamps, delete ---------------------------
        bottom = tk.Frame(self, bg=COLORS["bg"])
        bottom.pack(fill="x", pady=(8, 0))
        self.count_lbl = tk.Label(bottom, text="", bg=COLORS["bg"],
                                  fg=COLORS["faint"], font=FONTS["tiny"])
        self.count_lbl.pack(side="left")
        tk.Label(bottom,
                 text=f"Updated {note['updated'][:16]}",
                 bg=COLORS["bg"], fg=COLORS["faint"],
                 font=FONTS["tiny"]).pack(side="left", padx=(12, 0))

        if note["archived"]:
            text_button(bottom, "Delete forever", self.delete_forever,
                        COLORS["red"]).pack(side="right")
        else:
            text_button(bottom, "Delete", self.delete,
                        COLORS["red"]).pack(side="right")

        self.update_count()
        self.body.focus_set()

    # -- behavior ---------------------------------------------------------

    def load(self, note_id):
        """Open a note in the editor."""
        self.save_now()  # never lose the previous note's edits
        self.note_id = note_id
        self.note = db.get_note(note_id)
        if self.note:
            self._build_editor()
        else:
            self._build_empty()

    def new(self):
        """Create a note and open it."""
        self.save_now()
        self.note_id = db.create_note("Untitled")
        self.note = db.get_note(self.note_id)
        self._build_editor()
        self.on_change()
        self.title_entry.focus_set()
        self.title_entry.select_range(0, "end")

    def toggle(self, field):
        new_value = not self.note[field]
        db.set_flag(self.note_id, field, new_value)
        self.note[field] = 1 if new_value else 0
        self.refresh_toggles()
        self.mark_saved()
        self.on_change()

    def refresh_toggles(self):
        n = self.note
        self.pin_btn.configure(text="Unpin" if n["pinned"] else "Pin")
        self.fav_btn.configure(
            text="Unfavorite" if n["favorite"] else "Favorite")

    def restore(self):
        db.set_flag(self.note_id, "archived", False)
        self.on_change()
        self.load(self.note_id)

    def delete(self):
        if confirm_dialog(self, "Delete note",
                           "Move this note to the Archive?"):
            db.set_flag(self.note_id, "archived", True)
            self.note_id, self.note = None, None
            self._build_empty()
            self.on_change()

    def delete_forever(self):
        if confirm_dialog(self, "Delete forever",
                           "Permanently delete this note? This can't be undone."):
            db.delete_note(self.note_id)
            self.note_id, self.note = None, None
            self._build_empty()
            self.on_change()

    def schedule(self):
        """Debounced autosave: wait until the user pauses typing."""
        if self._timer:
            self.after_cancel(self._timer)
        self._timer = self.after(self.app.autosave_ms, self.save_now)
        self.update_count()

    def save_now(self):
        if not self.note_id or not self.note:
            return
        title = self.title_var.get().strip() or "Untitled"
        body = self.body.get("1.0", "end-1c")
        folder_name = self.folder_var.get()
        folder_id = next((f["id"] for f in db.list_folders()
                          if f["name"] == folder_name), None)
        # Skip the write if nothing actually changed.
        if (title == self.note["title"] and body == (self.note["body"] or "")
                and folder_id == self.note["folder_id"]):
            return
        db.update_note(self.note_id, title=title, body=body,
                       folder_id=folder_id)
        self.note.update(title=title, body=body, folder_id=folder_id)
        self.mark_saved()
        self.on_change()

    def mark_saved(self):
        if hasattr(self, "saved_lbl"):
            self.saved_lbl.configure(text="Saved")
            self.after(2000, lambda: self.saved_lbl.configure(text=""))

    def update_count(self):
        if not hasattr(self, "count_lbl"):
            return
        text = self.body.get("1.0", "end-1c")
        words = len(text.split())
        self.count_lbl.configure(text=f"{words} words · {len(text)} chars")


# -------------------------------------------------------- master-detail ---

class MasterDetail(tk.Frame):
    """Two-pane layout: note list left, editor right. Used by every
    list screen — only the title and the note query differ."""

    def __init__(self, parent, app, title, subtitle, fetch_notes,
                 select_id=None):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.fetch_notes = fetch_notes

        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(header, text=title, bg=COLORS["bg"], fg=COLORS["text"],
                 font=FONTS["display"]).pack(side="left")
        tk.Label(header, text=subtitle, bg=COLORS["bg"], fg=COLORS["muted"],
                 font=FONTS["small"]).pack(side="left", padx=(12, 0))
        primary_button(header, "New Note", self.new_note).pack(side="right")

        panes = tk.PanedWindow(self, bg=COLORS["bg"], sashwidth=6,
                               sashrelief="flat", orient="horizontal")
        panes.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        list_wrap = tk.Frame(panes, bg=COLORS["bg"], width=300)
        list_wrap.pack_propagate(False)
        panes.add(list_wrap, minsize=240)

        self.note_list = NoteList(list_wrap, self.open_note)
        self.note_list.pack(fill="both", expand=True)

        editor_wrap = tk.Frame(panes, bg=COLORS["bg"])
        panes.add(editor_wrap)
        self.editor = EditorPanel(editor_wrap, app, self.refresh)
        self.editor.pack(fill="both", expand=True)

        self.refresh(select_id=select_id)

    def refresh(self, select_id=None):
        """Reload the list; keep the current selection if it's still there."""
        notes = self.fetch_notes()
        current = select_id or self.editor.note_id
        self.note_list.show(notes)
        if not notes:
            self.editor._build_empty()
        elif current and any(n["id"] == current for n in notes):
            self.note_list.highlight(current)
            # Don't reload the editor while the user might be typing;
            # only load if it's a different note.
            if self.editor.note_id != current:
                self.editor.load(current)
        elif notes and self.editor.note_id is None:
            # Nothing open yet: show the first note.
            self.note_list.select(notes[0]["id"])

    def open_note(self, note_id):
        self.editor.load(note_id)

    def new_note(self):
        self.editor.new()


# ----------------------------------------------------------------- home ---

def greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def build_home(content, app):
    scroll_parent = tk.Frame(content, bg=COLORS["bg"])
    scroll_parent.pack(fill="both", expand=True)
    from .widgets import scrollable
    scroll = scrollable(scroll_parent)

    tk.Label(scroll, text=greeting(), bg=COLORS["bg"], fg=COLORS["text"],
             font=FONTS["display"]).pack(anchor="w", padx=24, pady=(20, 2))
    tk.Label(scroll, text="Here's what's happening with your notes today.",
             bg=COLORS["bg"], fg=COLORS["muted"],
             font=FONTS["body"]).pack(anchor="w", padx=24)

    # Simple stat tiles: number + label, no icons -------------------------
    stats = tk.Frame(scroll, bg=COLORS["bg"])
    stats.pack(fill="x", padx=24, pady=(18, 0))
    for i in range(4):
        stats.columnconfigure(i, weight=1, uniform="stat")

    tiles = [
        (db.count_notes(), "Total Notes", lambda: app.show("notes", mode="all")),
        (len(db.list_folders()), "Folders", lambda: app.show("folders")),
        (db.count_notes("archived = 0 AND pinned = 1"), "Pinned",
         lambda: app.show("notes", mode="pinned")),
        (db.count_notes("archived = 0 AND favorite = 1"), "Favorites",
         lambda: app.show("notes", mode="favorites")),
    ]
    for i, (number, label, cmd) in enumerate(tiles):
        tile = tk.Frame(stats, bg=COLORS["card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1, cursor="hand2")
        tile.grid(row=0, column=i, sticky="ew",
                  padx=(0, 12) if i < 3 else 0)
        tk.Label(tile, text=str(number), bg=COLORS["card"],
                 fg=COLORS["text"],
                 font=("Segoe UI", 22, "bold")).pack(
                     anchor="w", padx=16, pady=(14, 0))
        tk.Label(tile, text=label, bg=COLORS["card"], fg=COLORS["muted"],
                 font=FONTS["small"]).pack(anchor="w", padx=16, pady=(0, 14))
        tile.bind("<Button-1>", lambda _e, c=cmd: c())
        for child in tile.winfo_children():
            child.bind("<Button-1>", lambda _e, c=cmd: c())

    # Recent notes as a simple list ----------------------------------------
    header = tk.Frame(scroll, bg=COLORS["bg"])
    header.pack(fill="x", padx=24, pady=(26, 8))
    tk.Label(header, text="Recent Notes", bg=COLORS["bg"], fg=COLORS["text"],
             font=FONTS["heading"]).pack(side="left")
    primary_button(header, "New Note",
                   lambda: app.show("notes", mode="all", fresh=True)).pack(
                       side="right")

    notes = db.list_notes()[:6]
    if not notes:
        empty_state(scroll, "No notes yet",
                    "Click New Note to write your first one.")
        return

    for note in notes:
        row = tk.Frame(scroll, bg=COLORS["card"],
                       highlightbackground=COLORS["border"],
                       highlightthickness=1, cursor="hand2")
        row.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(row, text=note["title"] or "Untitled", bg=COLORS["card"],
                 fg=COLORS["text"], font=FONTS["title"],
                 anchor="w").pack(fill="x", padx=14, pady=(10, 0))
        tk.Label(row, text=relative_time(note["updated"]),
                 bg=COLORS["card"], fg=COLORS["faint"],
                 font=FONTS["tiny"], anchor="w").pack(
                     fill="x", padx=14, pady=(2, 10))
        nid = note["id"]
        row.bind("<Button-1>",
                 lambda _e, i=nid: app.show("notes", mode="all", select_id=i))
        for child in row.winfo_children():
            child.bind("<Button-1>",
                       lambda _e, i=nid: app.show("notes", mode="all",
                                                 select_id=i))


# --------------------------------------------------------------- folders ---

def build_folders(content, app):
    header = tk.Frame(content, bg=COLORS["bg"])
    header.pack(fill="x", padx=24, pady=(20, 12))
    tk.Label(header, text="Folders", bg=COLORS["bg"], fg=COLORS["text"],
             font=FONTS["display"]).pack(side="left")
    primary_button(header, "New Folder",
                   lambda: new_folder(app)).pack(side="right")

    folders = db.list_folders()
    if not folders:
        empty_state(content, "No folders yet",
                    "Create one to start organizing your notes.")
        return

    from .widgets import scrollable
    scroll = scrollable(content)
    for folder in folders:
        row = tk.Frame(scroll, bg=COLORS["card"],
                       highlightbackground=COLORS["border"],
                       highlightthickness=1, cursor="hand2")
        row.pack(fill="x", padx=24, pady=(0, 10))

        tk.Label(row, text=folder["name"], bg=COLORS["card"],
                 fg=COLORS["text"], font=FONTS["body"]).pack(
                     side="left", padx=14, pady=12)
        tk.Label(row, text=f"{folder['note_count']} notes", bg=COLORS["card"],
                 fg=COLORS["faint"], font=FONTS["small"]).pack(side="left")

        text_button(row, "Rename",
                    lambda f=folder: rename_folder(app, f)).pack(
                        side="right", padx=8)
        text_button(row, "Delete",
                    lambda f=folder: remove_folder(app, f),
                    COLORS["red"]).pack(side="right")

        fid = folder["id"]
        row.bind("<Button-1>",
                 lambda _e, i=fid: app.show("folder", folder_id=i))


def new_folder(app):
    name = input_dialog(app, "New folder", "Folder name:")
    if name:
        try:
            db.create_folder(name)
        except Exception:
            pass  # duplicate name; nothing to do
        app.refresh()


def rename_folder(app, folder):
    name = input_dialog(app, "Rename folder", "New name:",
                        initial=folder["name"])
    if name:
        db.rename_folder(folder["id"], name)
        app.refresh()


def remove_folder(app, folder):
    if confirm_dialog(app, "Delete folder",
                       f'Delete "{folder["name"]}"? Its notes become unfiled.'):
        db.delete_folder(folder["id"])
        app.refresh()


# ---------------------------------------------------------------- search ---

def build_search(content, app, query):
    md = MasterDetail(content, app,
                      title="Search",
                      subtitle=f'{len(db.search_notes(query))} result(s) for "{query}"',
                      fetch_notes=lambda: db.search_notes(query))
    md.pack(fill="both", expand=True)


# -------------------------------------------------------------- settings ---

def build_settings(content, app):
    from .widgets import scrollable
    tk.Label(content, text="Settings", bg=COLORS["bg"], fg=COLORS["text"],
             font=FONTS["display"]).pack(anchor="w", padx=24, pady=(20, 12))

    scroll = scrollable(content)
    body = tk.Frame(scroll, bg=COLORS["bg"])
    body.pack(fill="x", padx=24)

    card = tk.Frame(body, bg=COLORS["card"],
                    highlightbackground=COLORS["border"], highlightthickness=1)
    card.pack(fill="x", pady=(0, 16))

    row = tk.Frame(card, bg=COLORS["card"])
    row.pack(fill="x", padx=16, pady=12)
    tk.Label(row, text="Autosave after", bg=COLORS["card"],
             fg=COLORS["text"], font=FONTS["body"]).pack(side="left")
    delay_var = tk.StringVar(value=db.get_setting("autosave_ms", "1500"))
    tk.Entry(row, textvariable=delay_var, bg=COLORS["input"],
             fg=COLORS["text"], font=FONTS["body"],
             insertbackground=COLORS["text"], relief="flat",
             highlightbackground=COLORS["border"], highlightthickness=1,
             width=8).pack(side="right", ipady=4)
    tk.Label(row, text="ms of no typing", bg=COLORS["card"],
             fg=COLORS["muted"], font=FONTS["small"]).pack(side="right",
                                                           padx=(0, 8))

    def save_prefs():
        try:
            delay = max(500, int(delay_var.get()))
        except ValueError:
            delay = 1500
        db.set_setting("autosave_ms", str(delay))
        app.autosave_ms = delay

    primary_button(body, "Save", save_prefs).pack(anchor="w", pady=(0, 24))

    tk.Label(body, text="Notes — Capture. Organize. Create.\n"
                        "Built with Python, Tkinter, and SQLite.",
             bg=COLORS["bg"], fg=COLORS["muted"], font=FONTS["small"],
             justify="left").pack(anchor="w")
