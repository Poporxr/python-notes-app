"""SQLite storage for the notes app.

Plain functions, parameterized queries, no ORM. The tables are:
  folders    - named groups a note can belong to
  notes      - the notes themselves (pin/favorite/archive are flags)
  tags       - labels like "python"
  note_tags  - links notes to tags (many-to-many)
  settings   - simple key/value app preferences
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "notes.db")


def get_connection():
    """Open the database, creating the data folder if needed."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't exist yet. Safe to call every launch."""
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
               created TEXT DEFAULT (datetime('now')),
               updated TEXT DEFAULT (datetime('now')))"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS tags (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT UNIQUE NOT NULL)"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS note_tags (
               note_id INTEGER REFERENCES notes(id) ON DELETE CASCADE,
               tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
               PRIMARY KEY (note_id, tag_id))"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS settings (
               key TEXT PRIMARY KEY,
               value TEXT)"""
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- notes ---

def create_note(title="Untitled", body="", folder_id=None):
    """Insert a note and return its new id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notes (title, body, folder_id) VALUES (?, ?, ?)",
        (title, body, folder_id),
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


def update_note(note_id, title=None, body=None, folder_id=None):
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
    parts.append("updated = datetime('now')")
    values.append(note_id)
    cur.execute(f"UPDATE notes SET {', '.join(parts)} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_note(note_id):
    """Permanently delete a note (its tag links go with it)."""
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


def list_notes(mode="all", folder_id=None, tag_id=None, include_archived=False):
    """Notes for the list screens. Pinned notes come first, then newest."""
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM notes WHERE 1=1"
    params = []
    if not include_archived:
        query += " AND archived = 0"
    if mode == "pinned":
        query += " AND pinned = 1"
    elif mode == "favorites":
        query += " AND favorite = 1"
    elif mode == "archive":
        query = query.replace("AND archived = 0", "") + " AND archived = 1"
    if folder_id is not None:
        query += " AND folder_id = ?"
        params.append(folder_id)
    if tag_id is not None:
        query += " AND id IN (SELECT note_id FROM note_tags WHERE tag_id = ?)"
        params.append(tag_id)
    query += " ORDER BY pinned DESC, updated DESC"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def search_notes(text):
    """Find notes by title, body, or tag name."""
    conn = get_connection()
    cur = conn.cursor()
    like = f"%{text}%"
    cur.execute(
        """SELECT DISTINCT n.* FROM notes n
           LEFT JOIN note_tags nt ON nt.note_id = n.id
           LEFT JOIN tags t ON t.id = nt.tag_id
           WHERE n.archived = 0
             AND (n.title LIKE ? OR n.body LIKE ? OR t.name LIKE ?)
           ORDER BY n.pinned DESC, n.updated DESC""",
        (like, like, like),
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


# ----------------------------------------------------------------- tags ---

def get_or_create_tag(name):
    """Return the tag id, creating the tag if needed. Names are lowercase."""
    name = name.strip().lower().lstrip("#")
    if not name:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
    cur.execute("SELECT id FROM tags WHERE name = ?", (name,))
    tag_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return tag_id


def list_tags():
    """Tags with a live count of notes using each."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT t.*, (SELECT COUNT(*) FROM note_tags nt
                         JOIN notes n ON n.id = nt.note_id
                         WHERE nt.tag_id = t.id AND n.archived = 0) AS note_count
           FROM tags t ORDER BY t.name"""
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_tag(tag_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tags WHERE id = ?", (tag_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_note_tags(note_id):
    """Tag names attached to a note."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT t.name FROM tags t
           JOIN note_tags nt ON nt.tag_id = t.id
           WHERE nt.note_id = ? ORDER BY t.name""",
        (note_id,),
    )
    names = [r[0] for r in cur.fetchall()]
    conn.close()
    return names


def set_note_tags(note_id, tag_names):
    """Replace a note's tags with the given list of names."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
    for raw in tag_names:
        name = raw.strip().lower().lstrip("#")
        if not name:
            continue
        cur.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
        cur.execute("SELECT id FROM tags WHERE name = ?", (name,))
        tag_id = cur.fetchone()[0]
        cur.execute(
            "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)",
            (note_id, tag_id),
        )
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
    """Fill a fresh database with sample folders, tags, and notes so the
    app looks alive on first launch. Does nothing once notes exist."""
    if count_notes("1=1") > 0:
        return
    folder_ids = {}
    for name in ["Coding", "School", "Ideas", "Work", "Personal"]:
        folder_ids[name] = create_folder(name)

    samples = [
        ("Python Cheatsheet",
         "Basic syntax, data structures, functions, classes, and useful "
         "libraries for daily use.\n\n- Lists: [1, 2, 3]\n- Dicts: {'a': 1}\n"
         "- Loops: for x in items:",
         "Coding", ["python", "cheatsheet"], True, False),
        ("Project Ideas",
         "1. Studora (education app)\n2. Road travel (transport booking)\n"
         "3. Notes app with a really nice dark UI",
         "Ideas", ["ideas", "projects"], True, False),
        ("School Notes",
         "Key concepts from today's lecture:\n- Database normalization\n"
         "- SQL joins and relationships\n- Primary vs foreign keys",
         "School", ["school", "database"], False, False),
        ("Work Plan",
         "Q4 goals:\n- Finish Studora MVP\n- Improve app performance\n"
         "- Write documentation",
         "Work", ["work", "goals"], False, False),
        ("Personal Journal",
         "Life's been moving fast. Grateful for the progress, "
         "even if it feels slow sometimes.",
         "Personal", ["personal", "journal"], False, True),
        ("Welcome to Notes",
         "This is your new notes app.\n\n- Click New Note to start writing\n"
         "- Organize with folders and tags\n- Pin what matters with the star menu",
         None, ["important"], False, False),
    ]
    for title, body, folder, tags, pinned, favorite in samples:
        note_id = create_note(title, body,
                              folder_ids.get(folder) if folder else None)
        set_note_tags(note_id, tags)
        if pinned:
            set_flag(note_id, "pinned", True)
        if favorite:
            set_flag(note_id, "favorite", True)
