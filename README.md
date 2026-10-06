# Notes

A simple personal notes desktop app built with **Python, Tkinter, and SQLite**.
Dark-navy UI. No third-party packages — everything runs on the Python
standard library.

## Run it

```bash
python main.py
```

That's it. The database (`notes_app/data/notes.db`) is created automatically
on first launch, pre-filled with sample folders and notes so the app
feels alive right away.

## How it works

- **Sidebar** — Home, All Notes, Pinned, Favorites, Archive, Folders, Settings
- **Notes are lists** — click a note on the left, it opens on the right
- **Editor** — big title up top, body below, folder picker, pin/favorite/archive
  buttons, autosave, word count
- **Note types** — New Note asks what kind: Blank, Meeting notes, Todo list,
  or Journal entry, each with a starter template
- **Checklists** — type `- [ ]` for a task, click the box to check it off
- **Auto-lists** — Enter continues numbered and bulleted lists for you
- **Sort** — newest, oldest, or A–Z on any note list
- **Colors** — give a note an accent color, shown as an edge on its row
- **Export** — save any note as a `.txt` file
- **Folders** — create, rename, delete; notes become unfiled when a folder is deleted
- **Search** — the top bar searches titles and content
- **Shortcuts** — `Ctrl+N` new note, `Ctrl+F` search

## Project structure

```
main.py               # entry point: python main.py
notes_app/
├── main.py           # window, sidebar, search bar, screen switching
├── views.py          # all screens: home, master-detail lists, editor,
                      #   folders, search, settings
├── database.py       # SQLite: plain functions, parameterized queries
├── theme.py          # dark-navy palette and fonts
├── widgets.py        # small reusable pieces (buttons, dialogs, lists)
└── data/notes.db     # created automatically on first run
```

## Notes for class

Read `database.py` first (how notes are stored), then `views.py`
(how the master-detail layout works). Every function is small and
commented with why it exists.
