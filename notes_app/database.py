"""SQLite storage for the notes app.

Plain functions, parameterized queries, no ORM. Two tables:
  folders  - named groups a note can belong to
  notes    - the notes themselves (pin/favorite/archive are flags)
  settings - simple key/value app preferences

If this database was created by an older version of the app, the
leftover tags tables are dropped on startup (they only ever held
sample data).
"""

import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "notes.db")


def get_connection():
    """Open the database, creating the data folder if needed."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db():
    """Create tables if missing, drop the retired tags tables."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS folders (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT UNIQUE NOT NULL,
               created TEXT DEFAULT (datetime('now')))"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS notes (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               title TEXT NOT NULL DEFAULT 'Untitled',
               body TEXT DEFAULT '',
               folder_id INTEGER REFERENCES folders(id) ON DELETE SET NULL,
               pinned INTEGER DEFAULT 0,
               favorite INTEGER DEFAULT 0,
               archived INTEGER DEFAULT 0,
               color TEXT DEFAULT 'default',
               created TEXT DEFAULT (datetime('now')),
               updated TEXT DEFAULT (datetime('now')))"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS settings (
               key TEXT PRIMARY KEY,
               value TEXT)"""
    )
    # Tags were removed from the app; clean up after old installs.
    cur.execute("DROP TABLE IF EXISTS note_tags")
    cur.execute("DROP TABLE IF EXISTS tags")
    # Older installs lack the color column; add it if missing.
    cols = [r[1] for r in cur.execute("PRAGMA table_info(notes)")]
    if "color" not in cols:
        cur.execute("ALTER TABLE notes ADD COLUMN color TEXT DEFAULT 'default'")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- notes ---

def create_note(title="Untitled", body="", folder_id=None,
                created=None, updated=None, pinned=False, favorite=False):
    """Insert a note and return its new id.

    created/updated/pinned/favorite are only passed by the seed data so
    the sample notes look real; normal notes just stamp the current time."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notes (title, body, folder_id, created, updated,"
        " pinned, favorite) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, body, folder_id, created or now, updated or created or now,
         1 if pinned else 0, 1 if favorite else 0),
    )
    note_id = cur.lastrowid
    conn.commit()
    conn.close()
    return note_id


def get_note(note_id):
    """Fetch one note as a dict, or None."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_note(note_id, title=None, body=None, folder_id=None, color=None):
    """Update the given fields and stamp the note as edited."""
    conn = get_connection()
    cur = conn.cursor()
    parts, values = [], []
    if title is not None:
        parts.append("title = ?")
        values.append(title)
    if body is not None:
        parts.append("body = ?")
        values.append(body)
    if folder_id is not None:
        parts.append("folder_id = ?")
        values.append(folder_id)
    if color is not None:
        parts.append("color = ?")
        values.append(color)
    parts.append("updated = datetime('now')")
    values.append(note_id)
    cur.execute(f"UPDATE notes SET {', '.join(parts)} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_note(note_id):
    """Permanently delete a note."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()


def set_flag(note_id, field, value):
    """Flip pinned / favorite / archived on a note."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE notes SET {field} = ?, updated = datetime('now') WHERE id = ?",
        (1 if value else 0, note_id),
    )
    conn.commit()
    conn.close()


def list_notes(mode="all", folder_id=None):
    """Notes for the list screens. Pinned first, then newest."""
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM notes WHERE 1=1"
    params = []
    if mode == "archive":
        query += " AND archived = 1"
    else:
        query += " AND archived = 0"
        if mode == "pinned":
            query += " AND pinned = 1"
        elif mode == "favorites":
            query += " AND favorite = 1"
    if folder_id is not None:
        query += " AND folder_id = ?"
        params.append(folder_id)
    query += " ORDER BY pinned DESC, updated DESC"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def search_notes(text):
    """Find notes by title or body."""
    conn = get_connection()
    cur = conn.cursor()
    like = f"%{text}%"
    cur.execute(
        """SELECT * FROM notes
           WHERE archived = 0 AND (title LIKE ? OR body LIKE ?)
           ORDER BY pinned DESC, updated DESC""",
        (like, like),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def count_notes(where="archived = 0"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM notes WHERE {where}")
    n = cur.fetchone()[0]
    conn.close()
    return n


# -------------------------------------------------------------- folders ---

def create_folder(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO folders (name) VALUES (?)", (name.strip(),))
    folder_id = cur.lastrowid
    conn.commit()
    conn.close()
    return folder_id


def list_folders():
    """Folders with a live count of notes inside each."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT f.*, (SELECT COUNT(*) FROM notes n
                         WHERE n.folder_id = f.id AND n.archived = 0) AS note_count
           FROM folders f ORDER BY f.name"""
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_folder(folder_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM folders WHERE id = ?", (folder_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def rename_folder(folder_id, name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE folders SET name = ? WHERE id = ?", (name.strip(), folder_id))
    conn.commit()
    conn.close()


def delete_folder(folder_id):
    """Delete a folder; its notes become unfiled (not deleted)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE notes SET folder_id = NULL WHERE folder_id = ?", (folder_id,))
    cur.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
    conn.commit()
    conn.close()


# ------------------------------------------------------------- settings ---

def get_setting(key, default=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default


def set_setting(key, value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


# ------------------------------------------------------------ seed data ---

def seed_if_empty():
    """Fill a fresh database with sample folders and notes so the app
    looks alive on first launch. Does nothing once notes exist."""
    if count_notes("1=1") > 0:
        return
    folder_ids = {}
    for name in ["School", "Ideas", "Personal"]:
        folder_ids[name] = create_folder(name)

    def ago(days=0, hours=0):
        """A timestamp string for some time in the past, so the sample
        notes don't all claim to be brand new."""
        dt = datetime.now() - timedelta(days=days, hours=hours)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    samples = [
        # title, body, folder, pinned, favorite, created, updated
        ("Welcome to Notes",
         "This is your new notes app.\n\n- Click a note on the left to open it\n"
         "- Press New Note to start writing\n- Organize with folders\n- Pin what matters",
         None, False, False, ago(days=9), ago(days=9)),
        ("Q4 Goals",
         "- [ ] Finish Studora MVP\n- [ ] Improve app performance\n"
         "- [x] Write documentation\n- [ ] Ship the notes app",
         "Personal", False, False, ago(days=6), ago(days=4)),
        ("Database Normalization",
         "Key concepts from today's lecture:\n- First normal form: atomic values\n"
         "- Second normal form: no partial dependencies\n- Third normal form: no transitive dependencies",
         "School", False, True, ago(days=3), ago(days=3)),
        ("Project Ideas",
         "1. Studora (education app)\n2. Road travel (transport booking)\n"
         "3. Notes app with a really nice dark UI",
         "Ideas", True, False, ago(days=1), ago(hours=5)),
        ("Python Cheatsheet",
         "Basic syntax, data structures, functions, classes, and useful "
         "libraries for daily use.\n\n- Lists: [1, 2, 3]\n- Dicts: {'a': 1}\n"
         "- Loops: for x in items:",
         "School", True, False, ago(hours=2), ago(hours=2)),
    ]
    for title, body, folder, pinned, favorite, created, updated in samples:
        create_note(title, body,
                    folder_ids.get(folder) if folder else None,
                    created=created, updated=updated,
                    pinned=pinned, favorite=favorite)
