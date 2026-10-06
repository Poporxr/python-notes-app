# Notes — Capture. Organize. Create.

A polished personal notes desktop app built with **Python, Tkinter, and SQLite**.
Dark-navy UI inspired by modern notes apps. No third-party packages needed —
everything runs on the Python standard library.

## Run it

```bash
python main.py
```

That's it. The database (`notes_app/data/notes.db`) is created automatically
on first launch, pre-filled with sample folders, tags, and notes so the app
feels alive right away.

## Features

- Home dashboard with greeting, stat tiles, and recent notes
- Full note CRUD with a rich editor (autosave, word/character count)
- Folders (create, rename, delete)
- Tags (comma-separated in the editor, browsable per tag)
- Search across titles, content, and tags
- Pin, favorite, and archive notes (with restore)
- Keyboard shortcuts: `Ctrl+N` new note, `Ctrl+S` save, `Ctrl+F` search, `Delete`
- Settings: display name, autosave delay, database backup
- Confirmation dialogs for destructive actions
- Empty states everywhere

## Project structure

```
notes_app/
├── main.py            # window, sidebar, top bar, screen switching
├── theme.py           # dark-navy palette, fonts, icon symbols
├── database.py        # SQLite: plain functions, parameterized queries
├── widgets.py         # reusable cards, buttons, dialogs, skeletons
├── home_view.py       # dashboard
├── notes_views.py     # all / pinned / favorites / archive lists
├── editor_view.py     # note editor with autosave
├── organize_views.py  # folders, tags, search
└── settings_view.py   # preferences and data options
```

## Requirements

- Python 3.8+ (uses only the standard library: `tkinter`, `sqlite3`)
