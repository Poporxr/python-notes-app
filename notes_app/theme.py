"""Color palette and fonts. One dark-navy theme for the whole app."""

COLORS = {
    "bg": "#0e1320",        # main background
    "sidebar": "#141b2e",   # left navigation
    "card": "#182036",      # panels and list rows
    "card_hover": "#1f2942",  # row hover
    "selected": "#232e52",  # selected list row
    "border": "#232e4a",    # thin borders
    "input": "#101828",     # text entry background
    "text": "#e8ecf4",      # primary text
    "muted": "#8b94a7",     # secondary text
    "faint": "#5b6579",     # timestamps, hints
    "accent": "#6366f1",    # indigo primary buttons
    "accent_hover": "#5457e3",
    "accent_soft": "#262c52",  # selected nav background
    "green": "#34d399",
    "amber": "#fbbf24",
    "red": "#f87171",
}

FONTS = {
    "display": ("Segoe UI", 20, "bold"),  # screen titles, greeting
    "title": ("Segoe UI", 13, "bold"),    # note titles in lists
    "heading": ("Segoe UI", 11, "bold"),  # section labels
    "body": ("Segoe UI", 10),             # normal text
    "small": ("Segoe UI", 9),             # secondary text
    "tiny": ("Segoe UI", 8),              # timestamps
}

# Small text symbols for action buttons only (sidebar stays text-only).
# These are plain Unicode glyphs, not emoji, so they render everywhere.
ICONS = {
    "new": "+",
    "pin": "◉",
    "favorite": "★",
    "archive": "▦",
    "restore": "↩",
    "delete": "✕",
    "export": "↓",
    "sort": "⇅",
}

# Note accent colors. "default" means no accent (no colored edge).
NOTE_COLORS = {
    "blue": "#60a5fa",
    "green": "#34d399",
    "amber": "#fbbf24",
    "purple": "#a78bfa",
    "rose": "#fb7185",
}
COLOR_ORDER = ["default", "blue", "green", "amber", "purple", "rose"]
