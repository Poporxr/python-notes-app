"""Color palette, fonts, and icon symbols for the app.

Single dark-navy theme. Everything visual lives here so the whole app
stays consistent without hunting through files for color codes.
"""

# Dark navy palette taken from the design reference.
COLORS = {
    "bg": "#0e1320",        # main window background
    "sidebar": "#141b2e",   # left navigation panel
    "card": "#182036",      # note cards, stat cards, panels
    "card_hover": "#1f2942",  # card background on mouse hover
    "border": "#232e4a",    # thin borders around cards and inputs
    "input": "#101828",     # search bar and text entry background
    "text": "#e8ecf4",      # primary text
    "muted": "#8b94a7",      # secondary text
    "faint": "#5b6579",      # timestamps, placeholders
    "accent": "#6366f1",    # indigo primary buttons and highlights
    "accent_hover": "#5457e3",
    "accent_soft": "#262c52",  # soft indigo behind selected nav items
    "green": "#34d399",
    "amber": "#fbbf24",
    "pink": "#f472b6",
    "sky": "#38bdf8",
    "purple": "#a78bfa",
    "red": "#f87171",
}

# Colors cycled through for tag pills and tag dots.
TAG_COLORS = ["#6366f1", "#34d399", "#38bdf8", "#fbbf24", "#f472b6", "#a78bfa"]

# Colors for the folder icons in the sidebar.
FOLDER_COLORS = ["#6366f1", "#38bdf8", "#fbbf24", "#f472b6", "#34d399"]

FONTS = {
    "display": ("Segoe UI", 20, "bold"),   # "Good afternoon" greeting
    "title": ("Segoe UI", 13, "bold"),     # section headings
    "body": ("Segoe UI", 10),              # normal text
    "small": ("Segoe UI", 9),              # secondary text
    "tiny": ("Segoe UI", 8),               # timestamps, pills
    "logo": ("Segoe UI", 13, "bold"),
}

# Text symbols used as icons. Plain Unicode (not emoji) so they render
# the same on every operating system.
ICONS = {
    "logo": "\u25a4",        # ▤  app logo mark
    "home": "\u2302",        # ⌂
    "notes": "\u25a4",       # ▤
    "pin": "\u2316",         # ⌖
    "star": "\u2605",        # ★
    "archive": "\u25a6",     # ▦
    "folder": "\u25c9",      # ◉
    "tag_dot": "\u25cf",     # ●  colored dot before tag names
    "settings": "\u2699",    # ⚙
    "search": "\u2315",      # ⌕
    "plus": "\uff0b",        # ＋
    "close": "\u2715",       # ✕
    "clock": "\u25f7",       # ◷
    "dots": "\u22ee",        # ⋮  card menu
    "chevron": "\u203a",     # ›
    "back": "\u2039",        # ‹
    "check": "\u2713",       # ✓  saved indicator
}
