"""Main window: sidebar navigation, search bar, and screen switching."""

import tkinter as tk

from . import database as db
from .theme import COLORS, FONTS
from .widgets import clear, input_dialog
from . import views


class NotesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Notes")
        self.geometry("1280x800")
        self.minsize(1000, 640)
        self.configure(bg=COLORS["bg"])

        db.init_db()
        db.seed_if_empty()

        try:
            self.autosave_ms = int(db.get_setting("autosave_ms", "1500"))
        except ValueError:
            self.autosave_ms = 1500
        self.current = "home"
        self.current_args = {}

        # Sidebar -----------------------------------------------------------
        self.sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(side="left", fill="both", expand=True)

        # Top bar: search only (no account badge — there's no login) --------
        topbar = tk.Frame(main, bg=COLORS["bg"])
        topbar.pack(fill="x", padx=24, pady=(16, 0))
        search_wrap = tk.Frame(topbar, bg=COLORS["input"],
                               highlightbackground=COLORS["border"],
                               highlightthickness=1)
        search_wrap.pack(fill="x")
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_wrap, textvariable=self.search_var,
                                     bg=COLORS["input"], fg=COLORS["faint"],
                                     font=FONTS["body"],
                                     insertbackground=COLORS["text"],
                                     relief="flat", highlightthickness=0, bd=0)
        self.search_entry.pack(fill="x", ipady=8, padx=12)
        self.search_entry.insert(0, "Search notes...")
        self.search_entry.bind("<FocusIn>", self._clear_hint)
        self.search_entry.bind("<Return>", self._run_search)

        # Content area -------------------------------------------------------
        self.content = tk.Frame(main, bg=COLORS["bg"])
        self.content.pack(fill="both", expand=True)

        self.build_sidebar()
        self.show("home")

        self.bind("<Control-n>", lambda _e: self.new_note())
        self.bind("<Control-f>", lambda _e: self.focus_search())

    # -- sidebar ------------------------------------------------------------

    def nav_item(self, label, count=None, active=False, command=None):
        """One text-only row in the left navigation."""
        bg = COLORS["accent_soft"] if active else COLORS["sidebar"]
        fg = COLORS["text"] if active else COLORS["muted"]
        btn = tk.Frame(self.sidebar, bg=bg, cursor="hand2")
        btn.pack(fill="x", padx=8, pady=1)
        inner = tk.Frame(btn, bg=bg)
        inner.pack(fill="x", padx=12, pady=8)
        tk.Label(inner, text=label, bg=bg, fg=fg,
                 font=FONTS["body"]).pack(side="left")
        if count is not None:
            tk.Label(inner, text=str(count), bg=bg, fg=COLORS["faint"],
                     font=FONTS["small"]).pack(side="right")
        for w in (btn, inner, *inner.winfo_children()):
            w.bind("<Button-1>", lambda _e: command())

    def build_sidebar(self):
        clear(self.sidebar)
        tk.Label(self.sidebar, text="Notes", bg=COLORS["sidebar"],
                 fg=COLORS["text"], font=("Segoe UI", 15, "bold"),
                 anchor="w").pack(fill="x", padx=20, pady=(20, 16))

        items = [
            ("Home", None, self.current == "home",
             lambda: self.show("home")),
            ("All Notes", db.count_notes(), self.current == "notes"
             and self.current_args.get("mode", "all") == "all",
             lambda: self.show("notes", mode="all")),
            ("Pinned", db.count_notes("archived = 0 AND pinned = 1"),
             self.current == "notes"
             and self.current_args.get("mode") == "pinned",
             lambda: self.show("notes", mode="pinned")),
            ("Favorites", db.count_notes("archived = 0 AND favorite = 1"),
             self.current == "notes"
             and self.current_args.get("mode") == "favorites",
             lambda: self.show("notes", mode="favorites")),
            ("Archive", db.count_notes("archived = 1"),
             self.current == "notes"
             and self.current_args.get("mode") == "archive",
             lambda: self.show("notes", mode="archive")),
        ]
        for label, count, active, cmd in items:
            self.nav_item(label, count, active, cmd)

        tk.Label(self.sidebar, text="FOLDERS", bg=COLORS["sidebar"],
                 fg=COLORS["faint"], font=("Segoe UI", 8, "bold"),
                 anchor="w").pack(fill="x", padx=20, pady=(16, 4))
        for folder in db.list_folders():
            active = (self.current == "folder" and
                      self.current_args.get("folder_id") == folder["id"])
            fid = folder["id"]
            self.nav_item(folder["name"], folder["note_count"], active,
                          lambda f=fid: self.show("folder", folder_id=f))
        self.nav_item("+ New folder", None, False, self.new_folder)

        spacer = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        spacer.pack(fill="both", expand=True)
        self.nav_item("Settings", None, self.current == "settings",
                      lambda: self.show("settings"))

    def refresh(self):
        """Rebuild sidebar counts and the current screen."""
        self.build_sidebar()
        self.show(self.current, **self.current_args)

    def new_folder(self):
        name = input_dialog(self, "New folder", "Folder name:")
        if name:
            try:
                db.create_folder(name)
            except Exception:
                pass  # duplicate name
            self.refresh()

    # -- search ---------------------------------------------------------------

    def _clear_hint(self, _event=None):
        if self.search_var.get() == "Search notes...":
            self.search_var.set("")
            self.search_entry.configure(fg=COLORS["text"])

    def _run_search(self, _event=None):
        query = self.search_var.get().strip()
        if query and query != "Search notes...":
            self.show("search", query=query)

    def focus_search(self):
        self.search_entry.focus_set()
        self._clear_hint()

    def new_note(self):
        """Jump to All Notes and start a fresh note."""
        self.show("notes", mode="all", fresh=True)

    # -- screens -----------------------------------------------------------------

    TITLES = {
        "all": ("All Notes", "Every note that isn't archived."),
        "pinned": ("Pinned", "Notes you pinned for quick access."),
        "favorites": ("Favorites", "Notes you marked as favorites."),
        "archive": ("Archive", "Restore them or delete forever."),
    }

    def show(self, screen, **args):
        self.current = screen
        self.current_args = args
        clear(self.content)

        if screen == "home":
            views.build_home(self.content, self)
        elif screen == "notes":
            mode = args.get("mode", "all")
            title, subtitle = self.TITLES[mode]
            md = views.MasterDetail(
                self.content, self, title, subtitle,
                fetch_notes=lambda m=mode: db.list_notes(mode=m),
                select_id=args.get("select_id"))
            md.pack(fill="both", expand=True)
            if args.get("fresh"):
                md.new_note()
        elif screen == "folder":
            folder = db.get_folder(args.get("folder_id"))
            if not folder:
                self.show("folders")
                return
            md = views.MasterDetail(
                self.content, self, folder["name"],
                f'{folder["note_count"] if "note_count" in folder else ""} notes'
                .strip(),
                fetch_notes=lambda: db.list_notes(
                    folder_id=folder["id"]))
            md.pack(fill="both", expand=True)
        elif screen == "folders":
            views.build_folders(self.content, self)
        elif screen == "search":
            views.build_search(self.content, self, args.get("query", ""))
        elif screen == "settings":
            views.build_settings(self.content, self)

        self.build_sidebar()


def main():
    app = NotesApp()
    app.mainloop()


if __name__ == "__main__":
    main()
