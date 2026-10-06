"""Main window: sidebar navigation, top bar, and screen switching."""

import tkinter as tk

from . import database as db
from .theme import COLORS, FONTS, ICONS, FOLDER_COLORS
from .widgets import clear, sidebar_button, confirm_dialog, input_dialog
from .home_view import build_home
from .notes_views import build_notes_list
from .editor_view import build_editor
from .organize_views import (build_folders, build_folder_detail, build_tags,
                             build_tag_detail, build_search)
from .settings_view import build_settings


class NotesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Notes — Capture. Organize. Create.")
        self.geometry("1280x800")
        self.minsize(1000, 640)
        self.configure(bg=COLORS["bg"])

        db.init_db()
        db.seed_if_empty()

        # App-wide state every screen can read.
        self.user_name = db.get_setting("user_name", "Friend")
        try:
            self.autosave_ms = int(db.get_setting("autosave_ms", "1500"))
        except ValueError:
            self.autosave_ms = 1500
        self.current = "home"
        self.current_args = {}

        # Layout: sidebar on the left, everything else on the right. --------
        self.sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=232)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(side="left", fill="both", expand=True)

        # Top bar: search + avatar ------------------------------------------
        topbar = tk.Frame(main, bg=COLORS["bg"])
        topbar.pack(fill="x", padx=24, pady=(16, 0))

        search_wrap = tk.Frame(topbar, bg=COLORS["input"],
                               highlightbackground=COLORS["border"],
                               highlightthickness=1)
        search_wrap.pack(side="left", fill="x", expand=True)
        tk.Label(search_wrap, text=ICONS["search"], bg=COLORS["input"],
                 fg=COLORS["faint"], font=("Segoe UI", 11)).pack(
                     side="left", padx=(12, 4))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_wrap, textvariable=self.search_var,
                                     bg=COLORS["input"], fg=COLORS["text"],
                                     font=FONTS["body"],
                                     insertbackground=COLORS["text"],
                                     relief="flat", highlightthickness=0, bd=0)
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.search_entry.insert(0, "Search your notes, folders, or tags...")
        self.search_entry.configure(fg=COLORS["faint"])
        self.search_entry.bind("<FocusIn>", self._clear_search_hint)
        self.search_entry.bind("<Return>", self._run_search)

        avatar = tk.Frame(topbar, bg=COLORS["accent"], width=36, height=36)
        avatar.pack(side="right", padx=(16, 0))
        avatar.pack_propagate(False)
        self.avatar_lbl = tk.Label(avatar, text="N", bg=COLORS["accent"],
                                   fg="white", font=("Segoe UI", 13, "bold"))
        self.avatar_lbl.pack(expand=True)

        # Content area --------------------------------------------------------
        self.content = tk.Frame(main, bg=COLORS["bg"])
        self.content.pack(fill="both", expand=True)

        self.build_sidebar()
        self.show("home")

        # Global shortcuts ------------------------------------------------------
        self.bind("<Control-n>", lambda _e: self.show("editor"))
        self.bind("<Control-f>", lambda _e: self.focus_search())

    # ------------------------------------------------------------- sidebar ---

    def build_sidebar(self):
        """(Re)build the left navigation with live counts."""
        clear(self.sidebar)

        # Logo
        logo = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        logo.pack(fill="x", padx=16, pady=(20, 16))
        badge = tk.Frame(logo, bg=COLORS["accent"], width=34, height=34)
        badge.pack(side="left")
        badge.pack_propagate(False)
        tk.Label(badge, text=ICONS["logo"], bg=COLORS["accent"], fg="white",
                 font=("Segoe UI", 15)).pack(expand=True)
        text = tk.Frame(logo, bg=COLORS["sidebar"])
        text.pack(side="left", padx=(10, 0))
        tk.Label(text, text="Notes", bg=COLORS["sidebar"], fg=COLORS["text"],
                 font=FONTS["logo"]).pack(anchor="w")
        tk.Label(text, text="Capture. Organize. Create.", bg=COLORS["sidebar"],
                 fg=COLORS["faint"], font=FONTS["tiny"]).pack(anchor="w")

        # Main nav
        nav = [
            ("home", ICONS["home"], "Home", None),
            ("notes", ICONS["notes"], "All Notes", db.count_notes()),
            ("pinned", ICONS["pin"], "Pinned",
             db.count_notes("archived = 0 AND pinned = 1")),
            ("favorites", ICONS["star"], "Favorites",
             db.count_notes("archived = 0 AND favorite = 1")),
            ("archive", ICONS["archive"], "Archive",
             db.count_notes("archived = 1")),
        ]
        for key, icon, label, count in nav:
            active = self.current in (key,) or (
                key == "notes" and self.current == "notes")
            if key == "notes":
                cmd = lambda: self.show("notes", mode="all")
            elif key == "pinned":
                cmd = lambda: self.show("notes", mode="pinned")
            elif key == "favorites":
                cmd = lambda: self.show("notes", mode="favorites")
            elif key == "archive":
                cmd = lambda: self.show("notes", mode="archive")
            else:
                cmd = lambda k=key: self.show(k)
            sidebar_button(self.sidebar, icon, label, count,
                           active=active, command=cmd)

        # Folders
        fhead = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        fhead.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(fhead, text="Folders", bg=COLORS["sidebar"],
                 fg=COLORS["muted"], font=FONTS["small"]).pack(side="left")
        add_f = tk.Label(fhead, text=ICONS["plus"], bg=COLORS["sidebar"],
                         fg=COLORS["muted"], font=FONTS["small"], cursor="hand2")
        add_f.pack(side="right")
        add_f.bind("<Button-1>", lambda _e: self.new_folder())

        for i, folder in enumerate(db.list_folders()):
            color = FOLDER_COLORS[i % len(FOLDER_COLORS)]
            active = (self.current == "folder" and
                      self.current_args.get("folder_id") == folder["id"])
            btn = tk.Frame(self.sidebar, bg=COLORS["sidebar"], cursor="hand2")
            btn.pack(fill="x", padx=8, pady=1)
            inner = tk.Frame(btn, bg=COLORS["sidebar"])
            inner.pack(fill="x", padx=10, pady=6)
            tk.Label(inner, text=ICONS["folder"], bg=COLORS["sidebar"],
                     fg=color, font=("Segoe UI", 11), width=3).pack(side="left")
            tk.Label(inner, text=folder["name"], bg=COLORS["sidebar"],
                     fg=COLORS["muted"], font=FONTS["body"]).pack(side="left")
            tk.Label(inner, text=str(folder["note_count"]),
                     bg=COLORS["sidebar"], fg=COLORS["faint"],
                     font=FONTS["small"]).pack(side="right")
            fid = folder["id"]
            for w in (btn, inner):
                w.bind("<Button-1>",
                       lambda _e, f=fid: self.show("folder", folder_id=f))

        # Tags
        thead = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        thead.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(thead, text="Tags", bg=COLORS["sidebar"], fg=COLORS["muted"],
                 font=FONTS["small"]).pack(side="left")

        from .theme import TAG_COLORS
        for i, tag in enumerate(db.list_tags()):
            color = TAG_COLORS[i % len(TAG_COLORS)]
            active = (self.current == "tag" and
                      self.current_args.get("tag_id") == tag["id"])
            btn = tk.Frame(self.sidebar, bg=COLORS["sidebar"], cursor="hand2")
            btn.pack(fill="x", padx=8, pady=1)
            inner = tk.Frame(btn, bg=COLORS["sidebar"])
            inner.pack(fill="x", padx=10, pady=6)
            tk.Label(inner, text=ICONS["tag_dot"], bg=COLORS["sidebar"],
                     fg=color, font=("Segoe UI", 9), width=3).pack(side="left")
            tk.Label(inner, text=f"#{tag['name']}", bg=COLORS["sidebar"],
                     fg=COLORS["muted"], font=FONTS["body"]).pack(side="left")
            tk.Label(inner, text=str(tag["note_count"]),
                     bg=COLORS["sidebar"], fg=COLORS["faint"],
                     font=FONTS["small"]).pack(side="right")
            tid = tag["id"]
            for w in (btn, inner):
                w.bind("<Button-1>",
                       lambda _e, t=tid: self.show("tag", tag_id=t))

        # Settings pinned to the bottom
        spacer = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        spacer.pack(fill="both", expand=True)
        sidebar_button(self.sidebar, ICONS["settings"], "Settings",
                       active=self.current == "settings",
                       command=lambda: self.show("settings"))

        # Keep the avatar letter in sync with the name.
        self.avatar_lbl.configure(
            text=(self.user_name.strip()[:1] or "N").upper())

    def refresh_sidebar(self):
        self.build_sidebar()

    def new_folder(self):
        name = input_dialog(self, "New folder", "Folder name:")
        if name:
            try:
                db.create_folder(name)
            except Exception:
                pass  # duplicate name; nothing to do
            self.refresh_sidebar()
            if self.current == "folders":
                self.show("folders")

    # -------------------------------------------------------------- search ---

    def _clear_search_hint(self, _event=None):
        if self.search_var.get() == "Search your notes, folders, or tags...":
            self.search_var.set("")
            self.search_entry.configure(fg=COLORS["text"])

    def _run_search(self, _event=None):
        query = self.search_var.get().strip()
        if query and query != "Search your notes, folders, or tags...":
            self.show("search", query=query)

    def focus_search(self):
        self.search_entry.focus_set()
        self._clear_search_hint()

    # ------------------------------------------------------------- screens ---

    def show(self, screen, **args):
        """Swap the content area to a new screen."""
        self.current = screen
        self.current_args = args
        clear(self.content)
        # Unbind keys from the previous screen so they don't pile up.
        for seq in ("<Delete>", "<Control-s>"):
            try:
                self.content.unbind(seq)
            except tk.TclError:
                pass

        if screen == "home":
            build_home(self.content, self)
        elif screen == "notes":
            build_notes_list(self.content, self, mode=args.get("mode", "all"))
        elif screen == "editor":
            build_editor(self.content, self, note_id=args.get("note_id"))
        elif screen == "folders":
            build_folders(self.content, self)
        elif screen == "folder":
            build_folder_detail(self.content, self, args.get("folder_id"))
        elif screen == "tags":
            build_tags(self.content, self)
        elif screen == "tag":
            build_tag_detail(self.content, self, args.get("tag_id"))
        elif screen == "search":
            build_search(self.content, self, args.get("query", ""))
        elif screen == "settings":
            build_settings(self.content, self)

        self.build_sidebar()

    # ---------------------------------------------------------- note menu ---

    def note_menu(self, event, note):
        """The ⋮ popup menu on every note card."""
        menu = tk.Menu(self, tearoff=0, bg=COLORS["card"], fg=COLORS["text"],
                       activebackground=COLORS["accent"])
        menu.add_command(label="Open",
                         command=lambda: self.show("editor", note_id=note["id"]))
        menu.add_command(
            label="Unpin" if note["pinned"] else "Pin",
            command=lambda: self._flip(note["id"], "pinned", not note["pinned"]))
        menu.add_command(
            label="Remove from favorites" if note["favorite"] else "Add to favorites",
            command=lambda: self._flip(note["id"], "favorite", not note["favorite"]))
        if note["archived"]:
            menu.add_command(label="Restore",
                             command=lambda: self._flip(note["id"], "archived", False))
            menu.add_command(label="Delete forever",
                             command=lambda: self._delete(note["id"]))
        else:
            menu.add_command(label="Archive",
                             command=lambda: self._flip(note["id"], "archived", True))
            menu.add_command(label="Delete",
                             command=lambda: self._delete(note["id"]))
        menu.tk_popup(event.x_root, event.y_root)

    def _flip(self, note_id, field, value):
        db.set_flag(note_id, field, value)
        self.refresh_sidebar()
        self.show(self.current, **self.current_args)  # rebuild current screen

    def _delete(self, note_id):
        if confirm_dialog(self, "Delete note",
                           "Permanently delete this note? This can't be undone."):
            db.delete_note(note_id)
            self.refresh_sidebar()
            self.show("home")


def main():
    app = NotesApp()
    app.mainloop()


if __name__ == "__main__":
    main()
