"""Small reusable UI pieces so every screen looks like the same app.

Tkinter has no built-in "card" widget, so cards here are just Frames with
a thin border color and padding. Keep helpers small and honest.
"""

import tkinter as tk
from datetime import datetime

from .theme import COLORS, FONTS, ICONS, TAG_COLORS


def clear(frame):
    """Remove every widget from a frame (used when switching screens)."""
    for child in frame.winfo_children():
        child.destroy()


def section_label(parent, text):
    lbl = tk.Label(parent, text=text, bg=COLORS["bg"],
                   fg=COLORS["muted"], font=FONTS["small"])
    lbl.pack(anchor="w", pady=(18, 6), padx=2)
    return lbl


def sidebar_button(parent, icon, text, count=None, active=False, command=None):
    """One row in the left navigation. Highlights when it's the current screen."""
    bg = COLORS["accent_soft"] if active else COLORS["sidebar"]
    fg = COLORS["text"] if active else COLORS["muted"]
    btn = tk.Frame(parent, bg=bg, cursor="hand2")
    btn.pack(fill="x", padx=8, pady=1)

    inner = tk.Frame(btn, bg=bg)
    inner.pack(fill="x", padx=10, pady=7)
    tk.Label(inner, text=icon, bg=bg, fg=fg, font=("Segoe UI", 11),
             width=3).pack(side="left")
    tk.Label(inner, text=text, bg=bg, fg=fg, font=FONTS["body"]).pack(side="left")
    if count is not None:
        tk.Label(inner, text=str(count), bg=bg, fg=COLORS["faint"],
                 font=FONTS["small"]).pack(side="right")

    # Hover feedback, but never fight the active highlight.
    def on_enter(_e):
        if not active:
            btn.configure(bg=COLORS["card"])
            inner.configure(bg=COLORS["card"])
            for w in inner.winfo_children():
                w.configure(bg=COLORS["card"])

    def on_leave(_e):
        if not active:
            btn.configure(bg=COLORS["sidebar"])
            inner.configure(bg=COLORS["sidebar"])
            for w in inner.winfo_children():
                w.configure(bg=COLORS["sidebar"])

    for widget in (btn, inner):
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    if command:
        for widget in [btn, inner, *inner.winfo_children()]:
            widget.bind("<Button-1>", lambda _e: command())
    return btn


def stat_card(parent, icon, icon_bg, number, label, command=None):
    """One of the four dashboard stat tiles. Clickable like in the reference."""
    card = tk.Frame(parent, bg=COLORS["card"],
                    highlightbackground=COLORS["border"], highlightthickness=1,
                    cursor="hand2" if command else "")
    # Icon badge
    badge = tk.Frame(card, bg=icon_bg, width=34, height=34)
    badge.pack(anchor="w", padx=14, pady=(14, 0))
    badge.pack_propagate(False)
    tk.Label(badge, text=icon, bg=icon_bg, fg="white",
             font=("Segoe UI", 14)).pack(expand=True)

    row = tk.Frame(card, bg=COLORS["card"])
    row.pack(fill="x", padx=14, pady=(10, 4))
    tk.Label(row, text=str(number), bg=COLORS["card"], fg=COLORS["text"],
             font=("Segoe UI", 20, "bold")).pack(side="left")
    tk.Label(row, text=ICONS["chevron"], bg=COLORS["card"],
             fg=COLORS["faint"], font=("Segoe UI", 14)).pack(side="right")

    tk.Label(card, text=label, bg=COLORS["card"], fg=COLORS["muted"],
             font=FONTS["small"]).pack(anchor="w", padx=14, pady=(0, 14))

    def on_enter(_e):
        card.configure(bg=COLORS["card_hover"])
        for w in card.winfo_children():
            _recolor(w, COLORS["card_hover"])

    def on_leave(_e):
        card.configure(bg=COLORS["card"])
        for w in card.winfo_children():
            _recolor(w, COLORS["card"])

    def _recolor(widget, bg):
        # Only recolor plain card surfaces, never the icon badge or pills.
        if widget is badge or widget.winfo_parent() == str(badge):
            return
        try:
            if widget.cget("bg") in (COLORS["card"], COLORS["card_hover"]):
                widget.configure(bg=bg)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            _recolor(child, bg)

    if command:
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        card.bind("<Button-1>", lambda _e: command())
    return card


def tag_pill(parent, name, color=None):
    """Little rounded-looking #tag label used on note cards."""
    if color is None:
        color = TAG_COLORS[abs(hash(name)) % len(TAG_COLORS)]
    # Slightly transparent-looking background: mix the color with the card bg.
    lbl = tk.Label(parent, text=f"#{name}", bg=COLORS["card"],
                   fg=color, font=FONTS["tiny"], padx=8, pady=2,
                   highlightbackground=color, highlightthickness=1)
    return lbl


def note_card(parent, note, tags, accent_color, on_open, on_menu):
    """A note tile for the 2-column grid. Click opens, ⋮ opens actions."""
    card = tk.Frame(parent, bg=COLORS["card"],
                    highlightbackground=COLORS["border"], highlightthickness=1,
                    cursor="hand2")
    top = tk.Frame(card, bg=COLORS["card"])
    top.pack(fill="x", padx=12, pady=(12, 0))

    badge = tk.Frame(top, bg=accent_color, width=34, height=34)
    badge.pack(side="left")
    badge.pack_propagate(False)
    tk.Label(badge, text=ICONS["notes"], bg=accent_color, fg="white",
             font=("Segoe UI", 14)).pack(expand=True)

    title = tk.Label(top, text=note["title"] or "Untitled", bg=COLORS["card"],
                     fg=COLORS["text"], font=FONTS["body"], anchor="w")
    title.pack(side="left", fill="x", expand=True, padx=(10, 4))

    menu_btn = tk.Label(top, text=ICONS["dots"], bg=COLORS["card"],
                        fg=COLORS["muted"], font=("Segoe UI", 12), cursor="hand2")
    menu_btn.pack(side="right")
    menu_btn.bind("<Button-1>", lambda e: on_menu(e, note))

    preview = (note["body"] or "").replace("\n", " ").strip()
    if len(preview) > 110:
        preview = preview[:110] + "..."
    tk.Label(card, text=preview or "No content yet", bg=COLORS["card"],
             fg=COLORS["muted"], font=FONTS["small"], anchor="w",
             justify="left", wraplength=260).pack(fill="x", padx=12, pady=(6, 0))

    if tags:
        tag_row = tk.Frame(card, bg=COLORS["card"])
        tag_row.pack(fill="x", padx=12, pady=(8, 0))
        for t in tags[:3]:
            tag_pill(tag_row, t).pack(side="left", padx=(0, 6))

    bottom = tk.Frame(card, bg=COLORS["card"])
    bottom.pack(fill="x", padx=12, pady=(10, 12))
    tk.Label(bottom, text=f"{ICONS['clock']} {relative_time(note['updated'])}",
             bg=COLORS["card"], fg=COLORS["faint"], font=FONTS["tiny"]).pack(side="left")
    flags = []
    if note["pinned"]:
        flags.append(ICONS["pin"])
    if note["favorite"]:
        flags.append(ICONS["star"])
    if flags:
        tk.Label(bottom, text=" ".join(flags), bg=COLORS["card"],
                 fg=COLORS["amber"], font=FONTS["tiny"]).pack(side="right")

    def on_enter(_e):
        card.configure(bg=COLORS["card_hover"])

    def on_leave(_e):
        card.configure(bg=COLORS["card"])

    # Hover just tints the card frame; children keep their colors.
    card.bind("<Enter>", on_enter)
    card.bind("<Leave>", on_leave)
    card.bind("<Button-1>", lambda _e: on_open(note["id"]))
    title.bind("<Button-1>", lambda _e: on_open(note["id"]))
    return card


def relative_time(stamp):
    """'2 hours ago', 'Yesterday', 'Oct 4' — like the reference design."""
    try:
        dt = datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return ""
    delta = datetime.now() - dt
    if delta.days < 0:
        return "just now"
    if delta.days == 0:
        hours = delta.seconds // 3600
        if hours == 0:
            mins = max(1, delta.seconds // 60)
            return f"{mins} min ago" if mins > 1 else "just now"
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    if delta.days == 1:
        return "Yesterday"
    if delta.days < 7:
        return f"{delta.days} days ago"
    return dt.strftime("%b %d")


def empty_state(parent, icon, title, hint):
    """Friendly placeholder for screens with nothing to show yet."""
    box = tk.Frame(parent, bg=COLORS["bg"])
    box.pack(expand=True, fill="both", pady=60)
    tk.Label(box, text=icon, bg=COLORS["bg"], fg=COLORS["faint"],
             font=("Segoe UI", 32)).pack()
    tk.Label(box, text=title, bg=COLORS["bg"], fg=COLORS["text"],
             font=FONTS["title"]).pack(pady=(12, 4))
    tk.Label(box, text=hint, bg=COLORS["bg"], fg=COLORS["muted"],
             font=FONTS["small"]).pack()
    return box


def primary_button(parent, text, command):
    btn = tk.Label(parent, text=text, bg=COLORS["accent"], fg="white",
                   font=("Segoe UI", 10, "bold"), padx=18, pady=8, cursor="hand2")
    btn.bind("<Button-1>", lambda _e: command())
    btn.bind("<Enter>", lambda _e: btn.configure(bg=COLORS["accent_hover"]))
    btn.bind("<Leave>", lambda _e: btn.configure(bg=COLORS["accent"]))
    return btn


def ghost_button(parent, text, command):
    """Secondary button: bordered, transparent background."""
    btn = tk.Label(parent, text=text, bg=COLORS["bg"], fg=COLORS["muted"],
                   font=FONTS["body"], padx=14, pady=7, cursor="hand2",
                   highlightbackground=COLORS["border"], highlightthickness=1)
    btn.bind("<Button-1>", lambda _e: command())
    btn.bind("<Enter>", lambda _e: btn.configure(fg=COLORS["text"]))
    btn.bind("<Leave>", lambda _e: btn.configure(fg=COLORS["muted"]))
    return btn


def confirm_dialog(parent, title, message):
    """Yes/No dialog. Returns True when the user confirms."""
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.configure(bg=COLORS["card"])
    dlg.resizable(False, False)
    dlg.grab_set()  # block the main window until answered
    # Center over the parent window.
    dlg.update_idletasks()
    x = parent.winfo_rootx() + parent.winfo_width() // 2 - 160
    y = parent.winfo_rooty() + parent.winfo_height() // 2 - 70
    dlg.geometry(f"320x140+{x}+{y}")

    tk.Label(dlg, text=message, bg=COLORS["card"], fg=COLORS["text"],
             font=FONTS["body"], wraplength=280, justify="left").pack(
                 padx=20, pady=(20, 10))

    result = {"ok": False}
    row = tk.Frame(dlg, bg=COLORS["card"])
    row.pack(pady=10)

    def yes():
        result["ok"] = True
        dlg.destroy()

    tk.Label(row, text="Delete", bg=COLORS["red"], fg="white",
             font=("Segoe UI", 10, "bold"), padx=18, pady=6,
             cursor="hand2").pack(side="left", padx=6)
    row.winfo_children()[0].bind("<Button-1>", lambda _e: yes())
    cancel = tk.Label(row, text="Cancel", bg=COLORS["card"], fg=COLORS["muted"],
                      font=FONTS["body"], padx=18, pady=6, cursor="hand2",
                      highlightbackground=COLORS["border"], highlightthickness=1)
    cancel.pack(side="left", padx=6)
    cancel.bind("<Button-1>", lambda _e: dlg.destroy())

    dlg.bind("<Escape>", lambda _e: dlg.destroy())
    parent.wait_window(dlg)
    return result["ok"]


def input_dialog(parent, title, prompt, initial=""):
    """Single text-field dialog. Returns the typed text or None if cancelled."""
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.configure(bg=COLORS["card"])
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.update_idletasks()
    x = parent.winfo_rootx() + parent.winfo_width() // 2 - 160
    y = parent.winfo_rooty() + parent.winfo_height() // 2 - 70
    dlg.geometry(f"320x150+{x}+{y}")

    tk.Label(dlg, text=prompt, bg=COLORS["card"], fg=COLORS["muted"],
             font=FONTS["small"]).pack(anchor="w", padx=20, pady=(18, 6))
    entry = tk.Entry(dlg, bg=COLORS["input"], fg=COLORS["text"],
                     font=FONTS["body"], insertbackground=COLORS["text"],
                     highlightbackground=COLORS["border"], highlightthickness=1,
                     relief="flat")
    entry.pack(fill="x", padx=20)
    entry.insert(0, initial)
    entry.focus_set()
    entry.select_range(0, "end")

    result = {"value": None}
    row = tk.Frame(dlg, bg=COLORS["card"])
    row.pack(pady=14)

    def ok(_e=None):
        result["value"] = entry.get().strip() or None
        dlg.destroy()

    save = tk.Label(row, text="Save", bg=COLORS["accent"], fg="white",
                    font=("Segoe UI", 10, "bold"), padx=20, pady=6, cursor="hand2")
    save.pack(side="left", padx=6)
    save.bind("<Button-1>", ok)
    entry.bind("<Return>", ok)
    cancel = tk.Label(row, text="Cancel", bg=COLORS["card"], fg=COLORS["muted"],
                      font=FONTS["body"], padx=14, pady=6, cursor="hand2")
    cancel.pack(side="left", padx=6)
    cancel.bind("<Button-1>", lambda _e: dlg.destroy())
    dlg.bind("<Escape>", lambda _e: dlg.destroy())

    parent.wait_window(dlg)
    return result["value"]


def scrollable(parent):
    """A vertically scrollable area. Add widgets to the returned inner frame."""
    canvas = tk.Canvas(parent, bg=COLORS["bg"], highlightthickness=0)
    scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=COLORS["bg"])

    inner.bind("<Configure>",
               lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    window = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    def fit_width(event):
        canvas.itemconfig(window, width=event.width)

    canvas.bind("<Configure>", fit_width)

    def on_wheel(event):
        # Windows/Mac report different scroll units; both handled.
        delta = -1 if event.delta > 0 else 1
        if event.num in (4, 5):  # Linux
            delta = -1 if event.num == 4 else 1
        canvas.yview_scroll(delta, "units")

    canvas.bind_all("<MouseWheel>", on_wheel)
    canvas.bind_all("<Button-4>", on_wheel)
    canvas.bind_all("<Button-5>", on_wheel)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return inner
