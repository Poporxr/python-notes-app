"""Small reusable UI pieces. Plain functions, no classes."""

import tkinter as tk
from datetime import datetime

from .theme import COLORS, FONTS


def clear(frame):
    """Remove every widget from a frame (used when switching screens)."""
    for child in frame.winfo_children():
        child.destroy()


def empty_state(parent, title, hint):
    """Friendly placeholder for screens with nothing to show yet."""
    box = tk.Frame(parent, bg=COLORS["bg"])
    box.pack(expand=True, fill="both", pady=60)
    tk.Label(box, text=title, bg=COLORS["bg"], fg=COLORS["text"],
             font=FONTS["title"]).pack(pady=(12, 4))
    tk.Label(box, text=hint, bg=COLORS["bg"], fg=COLORS["muted"],
             font=FONTS["small"]).pack()
    return box


def primary_button(parent, text, command):
    """Indigo button."""
    btn = tk.Label(parent, text=text, bg=COLORS["accent"], fg="white",
                   font=("Segoe UI", 10, "bold"), padx=18, pady=8, cursor="hand2")
    btn.bind("<Button-1>", lambda _e: command())
    btn.bind("<Enter>", lambda _e: btn.configure(bg=COLORS["accent_hover"]))
    btn.bind("<Leave>", lambda _e: btn.configure(bg=COLORS["accent"]))
    return btn


def text_button(parent, text, command, color=None):
    """Plain text button, no icon."""
    btn = tk.Label(parent, text=text, bg=COLORS["bg"],
                   fg=color or COLORS["muted"], font=FONTS["small"],
                   cursor="hand2")
    btn.bind("<Button-1>", lambda _e: command())
    btn.bind("<Enter>", lambda _e: btn.configure(fg=COLORS["text"]))
    btn.bind("<Leave>", lambda _e: btn.configure(fg=color or COLORS["muted"]))
    return btn


def relative_time(stamp):
    """'2 hours ago', 'Yesterday', 'Oct 4'."""
    try:
        dt = datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return ""
    delta = datetime.now() - dt
    if delta.days <= 0:
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


def confirm_dialog(parent, title, message, ok_text="Delete"):
    """Yes/No dialog. Returns True when the user confirms."""
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.configure(bg=COLORS["card"])
    dlg.resizable(False, False)
    dlg.grab_set()
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

    ok_btn = tk.Label(row, text=ok_text, bg=COLORS["red"], fg="white",
                      font=("Segoe UI", 10, "bold"), padx=18, pady=6,
                      cursor="hand2")
    ok_btn.pack(side="left", padx=6)
    ok_btn.bind("<Button-1>", lambda _e: yes())
    cancel = tk.Label(row, text="Cancel", bg=COLORS["card"],
                      fg=COLORS["muted"], font=FONTS["body"],
                      padx=18, pady=6, cursor="hand2",
                      highlightbackground=COLORS["border"],
                      highlightthickness=1)
    cancel.pack(side="left", padx=6)
    cancel.bind("<Button-1>", lambda _e: dlg.destroy())

    dlg.bind("<Escape>", lambda _e: dlg.destroy())
    parent.wait_window(dlg)
    return result["ok"]


def input_dialog(parent, title, prompt, initial=""):
    """Single text-field dialog. Returns the typed text or None."""
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
                     highlightbackground=COLORS["border"],
                     highlightthickness=1, relief="flat")
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
                    font=("Segoe UI", 10, "bold"), padx=20, pady=6,
                    cursor="hand2")
    save.pack(side="left", padx=6)
    save.bind("<Button-1>", ok)
    entry.bind("<Return>", ok)
    cancel = tk.Label(row, text="Cancel", bg=COLORS["card"],
                      fg=COLORS["muted"], font=FONTS["body"],
                      padx=14, pady=6, cursor="hand2")
    cancel.pack(side="left", padx=6)
    cancel.bind("<Button-1>", lambda _e: dlg.destroy())
    dlg.bind("<Escape>", lambda _e: dlg.destroy())

    parent.wait_window(dlg)
    return result["value"]


def scrollable(parent):
    """A vertically scrollable area. Add widgets to the returned frame."""
    canvas = tk.Canvas(parent, bg=COLORS["bg"], highlightthickness=0)
    scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=COLORS["bg"])

    inner.bind("<Configure>",
               lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    window = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind("<Configure>",
                lambda e: canvas.itemconfig(window, width=e.width))

    def on_wheel(event):
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
