"""The note editor: title, body, tags, folder, pin/favorite, autosave."""

import tkinter as tk

from . import database as db
from .theme import COLORS, FONTS, ICONS
from .widgets import confirm_dialog, ghost_button, primary_button


def build_editor(content, app, note_id=None):
    note = db.get_note(note_id) if note_id else None
    is_new = note is None
    if is_new:
        # Create the row immediately so autosave always has an id to write to.
        note_id = db.create_note("Untitled")
        note = db.get_note(note_id)

    # Top bar -------------------------------------------------------------
    bar = tk.Frame(content, bg=COLORS["bg"])
    bar.pack(fill="x", padx=24, pady=(20, 0))
    back = tk.Label(bar, text=f"{ICONS['back']}  Back", bg=COLORS["bg"],
                    fg=COLORS["muted"], font=FONTS["body"], cursor="hand2")
    back.pack(side="left")
    back.bind("<Button-1>", lambda _e: (save_now(), app.show("home")))
    back.bind("<Enter>", lambda _e: back.configure(fg=COLORS["text"]))
    back.bind("<Leave>", lambda _e: back.configure(fg=COLORS["muted"]))

    saved_lbl = tk.Label(bar, text="", bg=COLORS["bg"], fg=COLORS["green"],
                         font=FONTS["small"])
    saved_lbl.pack(side="right", padx=(12, 0))

    def toggle_flag(field, btn, on_icon, off_icon):
        new_value = not note[field]
        db.set_flag(note_id, field, new_value)
        note[field] = 1 if new_value else 0
        btn.configure(text=on_icon if new_value else off_icon,
                      fg=COLORS["amber"] if new_value else COLORS["muted"])
        mark_saved()

    pin_btn = tk.Label(bar, text=ICONS["pin"] if note["pinned"] else ICONS["pin"],
                       bg=COLORS["bg"],
                       fg=COLORS["amber"] if note["pinned"] else COLORS["muted"],
                       font=("Segoe UI", 14), cursor="hand2")
    pin_btn.pack(side="right", padx=6)
    pin_btn.bind("<Button-1>",
                 lambda _e: toggle_flag("pinned", pin_btn, ICONS["pin"], ICONS["pin"]))

    fav_btn = tk.Label(bar, text=ICONS["star"], bg=COLORS["bg"],
                       fg=COLORS["amber"] if note["favorite"] else COLORS["muted"],
                       font=("Segoe UI", 14), cursor="hand2")
    fav_btn.pack(side="right", padx=6)
    fav_btn.bind("<Button-1>",
                 lambda _e: toggle_flag("favorite", fav_btn, ICONS["star"], ICONS["star"]))

    # Title ----------------------------------------------------------------
    title_var = tk.StringVar(value=note["title"])
    title_entry = tk.Entry(content, textvariable=title_var, bg=COLORS["bg"],
                           fg=COLORS["text"], font=FONTS["display"],
                           insertbackground=COLORS["text"], relief="flat",
                           highlightthickness=0, bd=0)
    title_entry.pack(fill="x", padx=24, pady=(16, 4))

    # Meta row: folder, tags, word count ------------------------------------
    meta = tk.Frame(content, bg=COLORS["bg"])
    meta.pack(fill="x", padx=24, pady=(0, 8))

    folders = db.list_folders()
    folder_names = ["No folder"] + [f["name"] for f in folders]
    current_folder = next((f["name"] for f in folders
                           if f["id"] == note["folder_id"]), "No folder")
    folder_var = tk.StringVar(value=current_folder)
    folder_menu = tk.OptionMenu(meta, folder_var, *folder_names)
    folder_menu.configure(bg=COLORS["card"], fg=COLORS["muted"],
                          font=FONTS["small"], relief="flat",
                          highlightbackground=COLORS["border"],
                          highlightthickness=1, padx=8)
    folder_menu["menu"].configure(bg=COLORS["card"], fg=COLORS["text"])
    folder_menu.pack(side="left")

    tags_var = tk.StringVar(value=", ".join(db.get_note_tags(note_id)))
    tk.Label(meta, text="Tags:", bg=COLORS["bg"], fg=COLORS["muted"],
             font=FONTS["small"]).pack(side="left", padx=(16, 4))
    tags_entry = tk.Entry(meta, textvariable=tags_var, bg=COLORS["input"],
                          fg=COLORS["text"], font=FONTS["small"],
                          insertbackground=COLORS["text"], relief="flat",
                          highlightbackground=COLORS["border"],
                          highlightthickness=1, width=28)
    tags_entry.pack(side="left", ipady=4)

    count_lbl = tk.Label(meta, text="", bg=COLORS["bg"], fg=COLORS["faint"],
                         font=FONTS["tiny"])
    count_lbl.pack(side="right")

    # Body ------------------------------------------------------------------
    body_frame = tk.Frame(content, bg=COLORS["card"],
                          highlightbackground=COLORS["border"],
                          highlightthickness=1)
    body_frame.pack(fill="both", expand=True, padx=24, pady=(0, 8))
    body_text = tk.Text(body_frame, bg=COLORS["card"], fg=COLORS["text"],
                        font=("Segoe UI", 11), insertbackground=COLORS["text"],
                        relief="flat", highlightthickness=0, bd=0,
                        wrap="word", padx=16, pady=16, undo=True)
    body_text.pack(fill="both", expand=True)
    body_text.insert("1.0", note["body"] or "")

    # Bottom bar --------------------------------------------------------------
    bottom = tk.Frame(content, bg=COLORS["bg"])
    bottom.pack(fill="x", padx=24, pady=(0, 20))
    info = tk.Label(bottom,
                    text=f"Created {note['created'][:10]}   ·   Updated {note['updated'][:16]}",
                    bg=COLORS["bg"], fg=COLORS["faint"], font=FONTS["tiny"])
    info.pack(side="left")

    def delete_current():
        if confirm_dialog(content, "Delete note",
                           "Permanently delete this note? This can't be undone."):
            db.delete_note(note_id)
            app.show("home")

    ghost_button(bottom, "Delete", delete_current).pack(side="right")
    save_btn = primary_button(bottom, "Save",
                              lambda: (save_now(), app.show("home")))
    save_btn.pack(side="right", padx=(0, 10))

    # Saving ------------------------------------------------------------------
    save_timer = {"id": None}

    def mark_saved():
        saved_lbl.configure(text=f"{ICONS['check']} Saved")
        content.after(2000, lambda: saved_lbl.configure(text=""))

    def save_now():
        """Write title, body, folder, and tags to the database."""
        title = title_var.get().strip() or "Untitled"
        body = body_text.get("1.0", "end-1c")
        folder_name = folder_var.get()
        folder_id = next((f["id"] for f in folders
                          if f["name"] == folder_name), None)
        db.update_note(note_id, title=title, body=body, folder_id=folder_id)
        db.set_note_tags(note_id, tags_var.get().split(","))
        note["title"] = title
        mark_saved()

    def schedule_save(_e=None):
        # Debounced autosave: wait until the user pauses typing.
        if save_timer["id"]:
            content.after_cancel(save_timer["id"])
        save_timer["id"] = content.after(app.autosave_ms, save_now)
        update_count()

    def update_count():
        words = body_text.get("1.0", "end-1c").split()
        chars = len(body_text.get("1.0", "end-1c"))
        count_lbl.configure(text=f"{len(words)} words · {chars} chars")

    title_entry.bind("<KeyRelease>", schedule_save)
    body_text.bind("<KeyRelease>", schedule_save)
    folder_var.trace_add("write", lambda *_: schedule_save())
    tags_entry.bind("<KeyRelease>", schedule_save)
    update_count()

    # Ctrl+S saves immediately. Delete removes the note, unless the user
    # is typing inside the editor (then Delete keeps its normal meaning).
    content.bind("<Control-s>", lambda _e: save_now())

    def on_delete_key(_e):
        if content.focus_get() not in (body_text, title_entry, tags_entry):
            delete_current()

    content.bind("<Delete>", on_delete_key)
    content.focus_set()
