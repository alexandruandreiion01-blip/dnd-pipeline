import tkinter as tk
from tkinter import ttk
import sqlite3
import os
from urllib.request import urlopen
from PIL import Image, ImageTk
import io
import threading
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# ── database ──────────────────────────────────────────────
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dnd.db")

# ── spell queries ──────────────────────────────────────────
def get_all_spell_names():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM spells ORDER BY name")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return names

def get_filter_options():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT school FROM spells ORDER BY school")
    schools = ["All"] + [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT damage_type FROM spells WHERE damage_type IS NOT NULL ORDER BY damage_type")
    damage_types = ["All"] + [row[0] for row in cursor.fetchall()]
    conn.close()
    classes = ["All", "Bard", "Cleric", "Druid", "Paladin",
               "Ranger", "Sorcerer", "Warlock", "Wizard"]
    levels = ["All"] + [str(i) for i in range(10)]
    return schools, damage_types, classes, levels

def search_spell(name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, level, school, classes, casting_time, range,
               concentration, ritual, damage_type, base_damage, description
        FROM spells WHERE LOWER(name) = LOWER(?)
    """, (name,))
    row = cursor.fetchone()
    conn.close()
    return row

def filter_spells(school="All", damage_type="All", class_="All", level="All"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT name, level, school, damage_type, classes FROM spells WHERE 1=1"
    params = []
    if school != "All":
        query += " AND school = ?"
        params.append(school)
    if damage_type != "All":
        query += " AND damage_type = ?"
        params.append(damage_type)
    if class_ != "All":
        query += " AND classes LIKE ?"
        params.append(f"%{class_}%")
    if level != "All":
        query += " AND level = ?"
        params.append(int(level))
    query += " ORDER BY level, name"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

# ── monster queries ────────────────────────────────────────
def get_all_monster_names():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM monsters ORDER BY name")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return names

def get_monster_filter_options():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT type FROM monsters WHERE type IS NOT NULL ORDER BY type")
    types = ["All"] + [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT challenge_rating FROM monsters ORDER BY challenge_rating")
    crs = ["All"] + [
        str(int(row[0])) if row[0] == int(row[0]) else str(row[0])
        for row in cursor.fetchall()
    ]
    sizes = ["All", "Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"]
    conn.close()
    return types, crs, sizes

def search_monster(name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, size, type, alignment, challenge_rating, xp,
               armor_class, hit_points, speed_walk,
               strength, dexterity, constitution,
               intelligence, wisdom, charisma,
               damage_immunities, damage_resistances, damage_vulnerabilities,
               damage_dealt, legendary, languages, image_url, description
        FROM monsters WHERE LOWER(name) = LOWER(?)
    """, (name,))
    row = cursor.fetchone()
    conn.close()
    return row

def filter_monsters(type_="All", cr="All", size="All", legendary_only=False):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT name, type, challenge_rating, hit_points, legendary FROM monsters WHERE 1=1"
    params = []
    if type_ != "All":
        query += " AND type = ?"
        params.append(type_)
    if cr != "All":
        query += " AND challenge_rating = ?"
        params.append(float(cr))
    if size != "All":
        query += " AND size = ?"
        params.append(size)
    if legendary_only:
        query += " AND legendary = 1"
    query += " ORDER BY challenge_rating, name"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

# ── analytics queries ──────────────────────────────────────
def get_damage_vs_monsters():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT damage_type FROM spells WHERE damage_type IS NOT NULL ORDER BY damage_type")
    damage_types = [row[0] for row in cursor.fetchall()]
    results = []
    for dt in damage_types:
        cursor.execute("SELECT COUNT(*) FROM monsters WHERE damage_immunities LIKE ?", (f"%{dt}%",))
        immune = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM monsters WHERE damage_resistances LIKE ?", (f"%{dt}%",))
        resistant = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM monsters WHERE damage_vulnerabilities LIKE ?", (f"%{dt}%",))
        vulnerable = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM spells WHERE damage_type = ?", (dt,))
        spell_count = cursor.fetchone()[0]
        results.append({
            "damage_type": dt,
            "immune":      immune,
            "resistant":   resistant,
            "vulnerable":  vulnerable,
            "spells":      spell_count,
            "score":       vulnerable - immune - (resistant * 0.5)
        })
    conn.close()
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

def get_school_stats():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT school,
               COUNT(*) as total,
               ROUND(AVG(level), 1) as avg_level,
               SUM(CASE WHEN damage_type IS NOT NULL THEN 1 ELSE 0 END) as damage_spells
        FROM spells
        GROUP BY school
        ORDER BY total DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_cr_distribution():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT challenge_rating, COUNT(*) as count
        FROM monsters
        WHERE challenge_rating <= 10
        GROUP BY challenge_rating
        ORDER BY challenge_rating
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

# ── colors & fonts ─────────────────────────────────────────
BG_DARK      = "#0d0d1a"
BG_CARD      = "#1a1a2e"
BG_INPUT     = "#16213e"
GOLD         = "#c9a84c"
GOLD_LIGHT   = "#f0d080"
TEXT         = "#e0e0e0"
TEXT_DIM     = "#888899"
PURPLE       = "#9370db"
RED          = "#cc3300"
BORDER       = "#2a2a4a"

FONT_TITLE   = ("Palatino Linotype", 22, "bold")
FONT_HEADING = ("Palatino Linotype", 13, "bold")
FONT_BODY    = ("Palatino Linotype", 11)
FONT_SMALL   = ("Palatino Linotype", 9)
FONT_INPUT   = ("Palatino Linotype", 12)

SCHOOL_COLORS = {
    "Evocation":    "#ff6633",
    "Necromancy":   "#9370db",
    "Illusion":     "#00bfff",
    "Conjuration":  "#32cd32",
    "Transmutation":"#ffd700",
    "Abjuration":   "#4169e1",
    "Enchantment":  "#ff69b4",
    "Divination":   "#87ceeb",
}

DAMAGE_COLORS = {
    "Fire":        "#ff4500",
    "Radiant":     "#ffd700",
    "Necrotic":    "#9370db",
    "Force":       "#00bfff",
    "Lightning":   "#7df9ff",
    "Cold":        "#add8e6",
    "Psychic":     "#ff69b4",
    "Bludgeoning": "#c8a87a",
    "Thunder":     "#9370db",
    "Piercing":    "#c0c0c0",
    "Acid":        "#7fff00",
    "Poison":      "#32cd32",
    "Slashing":    "#cd853f",
}

TYPE_COLORS = {
    "dragon":      "#ff4500",
    "undead":      "#9370db",
    "fiend":       "#cc3300",
    "celestial":   "#ffd700",
    "beast":       "#8b7355",
    "humanoid":    "#4169e1",
    "monstrosity": "#32cd32",
    "elemental":   "#00bfff",
    "construct":   "#c0c0c0",
    "fey":         "#ff69b4",
    "aberration":  "#7fff00",
    "giant":       "#c8a87a",
    "plant":       "#228b22",
    "ooze":        "#adff2f",
}

# ── spell card renderer ────────────────────────────────────
def render_spell_card(parent, spell):
    for w in parent.winfo_children():
        w.destroy()

    (name, level, school, classes, casting_time, range_,
     conc, ritual, damage_type, base_damage, description) = spell

    level_str  = "Cantrip" if level == 0 else f"Level {level}"
    school_col = SCHOOL_COLORS.get(school, GOLD)
    dmg_col    = DAMAGE_COLORS.get(damage_type, TEXT) if damage_type else TEXT

    canvas = tk.Canvas(parent, bg=BG_CARD, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG_CARD)
    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

    pad = {"padx": 20, "pady": 3}

    tk.Label(inner, text=name, font=("Palatino Linotype", 17, "bold"),
             bg=BG_CARD, fg=GOLD_LIGHT).pack(anchor="w", padx=20, pady=(16,2))

    pill = tk.Frame(inner, bg=BG_CARD)
    pill.pack(anchor="w", padx=20, pady=(0,8))
    tk.Label(pill, text=f"  {level_str}  ", font=FONT_SMALL,
             bg=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,6))
    tk.Label(pill, text=f"  {school}  ", font=FONT_SMALL,
             bg=school_col, fg=BG_DARK).pack(side="left")

    tk.Frame(inner, bg=GOLD, height=1).pack(fill="x", padx=20, pady=6)

    stats = [
        ("Casting Time", casting_time),
        ("Range",        range_),
        ("Concentration","Yes" if conc   else "No"),
        ("Ritual",       "Yes" if ritual else "No"),
    ]
    if damage_type:
        stats.append(("Damage", f"{base_damage}  {damage_type}"))

    grid = tk.Frame(inner, bg=BG_CARD)
    grid.pack(anchor="w", padx=20, pady=4)
    for i, (label, value) in enumerate(stats):
        tk.Label(grid, text=label + ":", font=FONT_SMALL,
                 bg=BG_CARD, fg=TEXT_DIM, width=14,
                 anchor="w").grid(row=i, column=0, sticky="w", pady=1)
        col = dmg_col if label == "Damage" else TEXT
        tk.Label(grid, text=value, font=FONT_SMALL,
                 bg=BG_CARD, fg=col, anchor="w").grid(row=i, column=1, sticky="w", pady=1)

    tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=20, pady=8)
    tk.Label(inner, text="Classes", font=FONT_HEADING,
             bg=BG_CARD, fg=GOLD).pack(anchor="w", **pad)
    tk.Label(inner, text=classes, font=FONT_BODY,
             bg=BG_CARD, fg=TEXT, wraplength=600,
             justify="left").pack(anchor="w", **pad)

    tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=20, pady=8)
    tk.Label(inner, text="Description", font=FONT_HEADING,
             bg=BG_CARD, fg=GOLD).pack(anchor="w", **pad)
    tk.Label(inner, text=description, font=FONT_BODY,
             bg=BG_CARD, fg=TEXT, wraplength=600,
             justify="left").pack(anchor="w", padx=20, pady=(3,20))

# ── monster card renderer ──────────────────────────────────
def render_monster_card(parent, monster):
    for w in parent.winfo_children():
        w.destroy()

    (name, size, type_, alignment, cr, xp, ac, hp, speed,
     str_, dex, con, int_, wis, cha,
     immunities, resistances, vulnerabilities,
     damage_dealt, legendary, languages, image_url, description) = monster

    type_col = TYPE_COLORS.get(type_, GOLD)
    legendary_str = "⭐ Legendary" if legendary else ""

    canvas = tk.Canvas(parent, bg=BG_CARD, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG_CARD)
    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

    pad = {"padx": 20, "pady": 3}

    top = tk.Frame(inner, bg=BG_CARD)
    top.pack(fill="x", padx=20, pady=(16,4))

    left = tk.Frame(top, bg=BG_CARD)
    left.pack(side="left", anchor="n", fill="x", expand=True)

    tk.Label(left, text=name, font=("Palatino Linotype", 17, "bold"),
             bg=BG_CARD, fg=GOLD_LIGHT).pack(anchor="w")

    if legendary_str:
        tk.Label(left, text=legendary_str, font=FONT_SMALL,
                 bg=BG_CARD, fg=GOLD).pack(anchor="w", pady=(2,4))

    pill = tk.Frame(left, bg=BG_CARD)
    pill.pack(anchor="w", pady=(2,8))
    tk.Label(pill, text=f"  CR {cr}  ", font=FONT_SMALL,
             bg=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,6))
    tk.Label(pill, text=f"  {type_}  ", font=FONT_SMALL,
             bg=type_col, fg=BG_DARK).pack(side="left", padx=(0,6))
    tk.Label(pill, text=f"  {size}  ", font=FONT_SMALL,
             bg=BG_INPUT, fg=TEXT_DIM).pack(side="left")

    img_label = tk.Label(top, bg=BG_CARD, text="Loading...",
                         font=FONT_SMALL, fg=TEXT_DIM)
    img_label.pack(side="right", anchor="n", padx=(8,0))

    def fetch_image():
        try:
            with urlopen(image_url, timeout=5) as response:
                img_data = response.read()
            img = Image.open(io.BytesIO(img_data))
            img.thumbnail((160, 160))
            photo = ImageTk.PhotoImage(img)
            try:
                img_label.config(image=photo, text="")
                img_label.image = photo
            except Exception:
                pass
        except Exception:
            try:
                img_label.config(text="No image")
            except Exception:
                pass

    threading.Thread(target=fetch_image, daemon=True).start()

    tk.Frame(inner, bg=GOLD, height=1).pack(fill="x", padx=20, pady=6)

    stats = [
        ("Alignment",  alignment or "—"),
        ("AC",         str(ac) if ac else "—"),
        ("Hit Points", str(hp) if hp else "—"),
        ("Speed",      f"{speed} ft." if speed else "—"),
        ("XP",         str(xp) if xp else "—"),
    ]
    grid = tk.Frame(inner, bg=BG_CARD)
    grid.pack(anchor="w", padx=20, pady=4)
    for i, (label, value) in enumerate(stats):
        tk.Label(grid, text=label + ":", font=FONT_SMALL,
                 bg=BG_CARD, fg=TEXT_DIM, width=14,
                 anchor="w").grid(row=i, column=0, sticky="w", pady=1)
        tk.Label(grid, text=value, font=FONT_SMALL,
                 bg=BG_CARD, fg=TEXT,
                 anchor="w").grid(row=i, column=1, sticky="w", pady=1)

    tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=20, pady=8)
    tk.Label(inner, text="Ability Scores", font=FONT_HEADING,
             bg=BG_CARD, fg=GOLD).pack(anchor="w", **pad)

    scores_frame = tk.Frame(inner, bg=BG_CARD)
    scores_frame.pack(anchor="w", padx=20, pady=4)
    abilities = [("STR", str_), ("DEX", dex), ("CON", con),
                 ("INT", int_), ("WIS", wis), ("CHA", cha)]
    for i, (ab, val) in enumerate(abilities):
        f = tk.Frame(scores_frame, bg=BG_INPUT, padx=10, pady=6)
        f.grid(row=0, column=i, padx=4)
        modifier = (val - 10) // 2
        mod_str = f"+{modifier}" if modifier >= 0 else str(modifier)
        tk.Label(f, text=ab, font=FONT_SMALL, bg=BG_INPUT, fg=TEXT_DIM).pack()
        tk.Label(f, text=str(val), font=FONT_HEADING, bg=BG_INPUT, fg=TEXT).pack()
        tk.Label(f, text=mod_str, font=FONT_SMALL, bg=BG_INPUT, fg=GOLD).pack()

    tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=20, pady=8)
    damage_info = [
        ("Immunities",      immunities,      "#888899"),
        ("Resistances",     resistances,     "#4169e1"),
        ("Vulnerabilities", vulnerabilities, "#cc3300"),
        ("Deals",           damage_dealt,    "#ff4500"),
    ]
    for label, value, color in damage_info:
        if value:
            row_f = tk.Frame(inner, bg=BG_CARD)
            row_f.pack(anchor="w", padx=20, pady=2)
            tk.Label(row_f, text=f"{label}:", font=FONT_SMALL,
                     bg=BG_CARD, fg=TEXT_DIM, width=14,
                     anchor="w").pack(side="left")
            tk.Label(row_f, text=value, font=FONT_SMALL,
                     bg=BG_CARD, fg=color,
                     wraplength=500, justify="left").pack(side="left")

    if languages:
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=20, pady=8)
        tk.Label(inner, text="Languages", font=FONT_HEADING,
                 bg=BG_CARD, fg=GOLD).pack(anchor="w", **pad)
        tk.Label(inner, text=languages, font=FONT_BODY,
                 bg=BG_CARD, fg=TEXT, wraplength=600,
                 justify="left").pack(anchor="w", **pad)

    if description:
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=20, pady=8)
        tk.Label(inner, text="Description", font=FONT_HEADING,
                 bg=BG_CARD, fg=GOLD).pack(anchor="w", **pad)
        tk.Label(inner, text=description, font=FONT_BODY,
                 bg=BG_CARD, fg=TEXT, wraplength=600,
                 justify="left").pack(anchor="w", padx=20, pady=(3,20))

# ── main app ───────────────────────────────────────────────
class SpellbookApp:
    def __init__(self, root):
        self.root = root
        self.root.title("D&D 5e Tome")
        self.root.configure(bg=BG_DARK)
        self.root.geometry("960x720")
        self.root.resizable(True, True)
        self.all_spells   = get_all_spell_names()
        self.all_monsters = get_all_monster_names()
        self.schools, self.damage_types, self.classes, self.levels = get_filter_options()
        self.monster_types, self.monster_crs, self.monster_sizes = get_monster_filter_options()
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG_DARK)
        header.pack(fill="x", padx=24, pady=(16,0))
        tk.Label(header, text="✦  Tome of Arcane Knowledge  ✦",
                 font=FONT_TITLE, bg=BG_DARK, fg=GOLD).pack()
        tk.Label(header, text="D&D 5e Spell & Bestiary Analytics",
                 font=FONT_SMALL, bg=BG_DARK, fg=TEXT_DIM).pack()
        tk.Frame(self.root, bg=GOLD, height=1).pack(fill="x", padx=24, pady=8)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_INPUT,
                        foreground=TEXT_DIM, padding=[16, 6], font=FONT_BODY)
        style.map("TNotebook.Tab",
                  background=[("selected", BG_CARD)],
                  foreground=[("selected", GOLD)])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=24, pady=(0,16))

        self.tab_search   = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_browse   = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_bestiary = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_analytics = tk.Frame(self.notebook, bg=BG_DARK)

        self.notebook.add(self.tab_search,    text="  🔍 Spell Search  ")
        self.notebook.add(self.tab_browse,    text="  📖 Spell Browse  ")
        self.notebook.add(self.tab_bestiary,  text="  🐉 Bestiary  ")
        self.notebook.add(self.tab_analytics, text="  📊 Analytics  ")

        self._build_search_tab()
        self._build_browse_tab()
        self._build_bestiary_tab()
        self._build_analytics_tab()

    # ── TAB 1: Spell Search ────────────────────────────────
    def _build_search_tab(self):
        top = tk.Frame(self.tab_search, bg=BG_DARK)
        top.pack(fill="x", pady=10)

        tk.Label(top, text="Spell Name:", font=FONT_BODY,
                 bg=BG_DARK, fg=TEXT_DIM).pack(side="left", padx=(0,8))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_type)

        self.entry = tk.Entry(top, textvariable=self.search_var,
                              font=FONT_INPUT, bg=BG_INPUT, fg=TEXT,
                              insertbackground=GOLD, relief="flat",
                              highlightthickness=1, highlightcolor=GOLD,
                              highlightbackground=BORDER, width=32)
        self.entry.pack(side="left", ipady=6, padx=(0,8))
        self.entry.bind("<Return>", lambda e: self._do_search())
        self.entry.bind("<Down>",   lambda e: self._focus_dropdown())

        tk.Button(top, text="Search", font=FONT_BODY,
                  bg=GOLD, fg=BG_DARK, activebackground=GOLD_LIGHT,
                  relief="flat", padx=14, pady=4,
                  command=self._do_search).pack(side="left")

        self.dropdown_frame = tk.Frame(self.root, bg=BG_CARD,
                                       highlightthickness=1,
                                       highlightbackground=GOLD)
        self.listbox = tk.Listbox(self.dropdown_frame, font=FONT_BODY,
                                  bg=BG_CARD, fg=TEXT,
                                  selectbackground=GOLD,
                                  selectforeground=BG_DARK,
                                  relief="flat", height=5, activestyle="none")
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Return>",   lambda e: self._select_from_dropdown())
        self.listbox.bind("<Double-1>", lambda e: self._select_from_dropdown())
        self.listbox.bind("<Escape>",   lambda e: self._hide_dropdown())
        self.dropdown_frame.place_forget()

        self.card = tk.Frame(self.tab_search, bg=BG_CARD,
                             highlightthickness=1, highlightbackground=BORDER)
        self.card.pack(fill="both", expand=True)
        tk.Label(self.card,
                 text="✦\n\nSearch for a spell above\nto reveal its secrets",
                 font=FONT_BODY, bg=BG_CARD, fg=TEXT_DIM,
                 justify="center").pack(expand=True)

    # ── TAB 2: Spell Browse ────────────────────────────────
    def _build_browse_tab(self):
        filter_bar = tk.Frame(self.tab_browse, bg=BG_DARK)
        filter_bar.pack(fill="x", pady=10)

        def make_dropdown(label, options, var, callback):
            tk.Label(filter_bar, text=label, font=FONT_SMALL,
                     bg=BG_DARK, fg=TEXT_DIM).pack(side="left", padx=(8,2))
            cb = ttk.Combobox(filter_bar, textvariable=var,
                              values=options, state="readonly",
                              width=14, font=FONT_SMALL)
            cb.pack(side="left", padx=(0,4))
            cb.bind("<<ComboboxSelected>>", lambda e: callback())
            return cb

        self.filter_school  = tk.StringVar(value="All")
        self.filter_damage  = tk.StringVar(value="All")
        self.filter_class   = tk.StringVar(value="All")
        self.filter_level   = tk.StringVar(value="All")

        make_dropdown("School:",  self.schools,      self.filter_school,  self._apply_spell_filters)
        make_dropdown("Damage:",  self.damage_types, self.filter_damage,  self._apply_spell_filters)
        make_dropdown("Class:",   self.classes,      self.filter_class,   self._apply_spell_filters)
        make_dropdown("Level:",   self.levels,       self.filter_level,   self._apply_spell_filters)

        tk.Button(filter_bar, text="Reset", font=FONT_SMALL,
                  bg=BG_INPUT, fg=TEXT_DIM, relief="flat", padx=8,
                  command=self._reset_spell_filters).pack(side="left", padx=8)

        self.spell_result_count = tk.Label(filter_bar, text="",
                                           font=FONT_SMALL, bg=BG_DARK, fg=TEXT_DIM)
        self.spell_result_count.pack(side="right", padx=12)

        split = tk.Frame(self.tab_browse, bg=BG_DARK)
        split.pack(fill="both", expand=True)

        list_frame = tk.Frame(split, bg=BG_CARD,
                              highlightthickness=1, highlightbackground=BORDER)
        list_frame.pack(side="left", fill="both", padx=(0,4))
        list_frame.pack_propagate(False)
        list_frame.configure(width=240)

        list_scroll = ttk.Scrollbar(list_frame, orient="vertical")
        self.spell_listbox = tk.Listbox(list_frame, font=FONT_SMALL,
                                        bg=BG_CARD, fg=TEXT,
                                        selectbackground=GOLD,
                                        selectforeground=BG_DARK,
                                        relief="flat", activestyle="none",
                                        yscrollcommand=list_scroll.set)
        list_scroll.config(command=self.spell_listbox.yview)
        list_scroll.pack(side="right", fill="y")
        self.spell_listbox.pack(fill="both", expand=True)
        self.spell_listbox.bind("<<ListboxSelect>>", self._on_spell_list_select)

        self.browse_card = tk.Frame(split, bg=BG_CARD,
                                    highlightthickness=1,
                                    highlightbackground=BORDER)
        self.browse_card.pack(side="left", fill="both", expand=True)
        tk.Label(self.browse_card,
                 text="✦\n\nSelect a spell from the list",
                 font=FONT_BODY, bg=BG_CARD, fg=TEXT_DIM,
                 justify="center").pack(expand=True)

        self._apply_spell_filters()

    # ── TAB 3: Bestiary ────────────────────────────────────
    def _build_bestiary_tab(self):
        search_row = tk.Frame(self.tab_bestiary, bg=BG_DARK)
        search_row.pack(fill="x", pady=(10,0))

        tk.Label(search_row, text="Monster Name:", font=FONT_BODY,
                 bg=BG_DARK, fg=TEXT_DIM).pack(side="left", padx=(0,8))

        self.monster_search_var = tk.StringVar()
        self.monster_search_var.trace_add("write", self._on_monster_type)

        self.monster_entry = tk.Entry(search_row,
                                      textvariable=self.monster_search_var,
                                      font=FONT_INPUT, bg=BG_INPUT, fg=TEXT,
                                      insertbackground=GOLD, relief="flat",
                                      highlightthickness=1, highlightcolor=GOLD,
                                      highlightbackground=BORDER, width=32)
        self.monster_entry.pack(side="left", ipady=6, padx=(0,8))
        self.monster_entry.bind("<Return>", lambda e: self._do_monster_search())
        self.monster_entry.bind("<Down>",   lambda e: self._focus_monster_dropdown())

        tk.Button(search_row, text="Search", font=FONT_BODY,
                  bg=GOLD, fg=BG_DARK, activebackground=GOLD_LIGHT,
                  relief="flat", padx=14, pady=4,
                  command=self._do_monster_search).pack(side="left")

        self.monster_dropdown_frame = tk.Frame(self.root, bg=BG_CARD,
                                               highlightthickness=1,
                                               highlightbackground=GOLD)
        self.monster_listbox_auto = tk.Listbox(self.monster_dropdown_frame,
                                               font=FONT_BODY, bg=BG_CARD, fg=TEXT,
                                               selectbackground=GOLD,
                                               selectforeground=BG_DARK,
                                               relief="flat", height=5,
                                               activestyle="none")
        self.monster_listbox_auto.pack(fill="both", expand=True)
        self.monster_listbox_auto.bind("<Return>",   lambda e: self._select_from_monster_dropdown())
        self.monster_listbox_auto.bind("<Double-1>", lambda e: self._select_from_monster_dropdown())
        self.monster_listbox_auto.bind("<Escape>",   lambda e: self._hide_monster_dropdown())
        self.monster_dropdown_frame.place_forget()

        filter_bar = tk.Frame(self.tab_bestiary, bg=BG_DARK)
        filter_bar.pack(fill="x", pady=(6,0))

        def make_dropdown(label, options, var, callback):
            tk.Label(filter_bar, text=label, font=FONT_SMALL,
                     bg=BG_DARK, fg=TEXT_DIM).pack(side="left", padx=(8,2))
            cb = ttk.Combobox(filter_bar, textvariable=var,
                              values=options, state="readonly",
                              width=12, font=FONT_SMALL)
            cb.pack(side="left", padx=(0,4))
            cb.bind("<<ComboboxSelected>>", lambda e: callback())
            return cb

        self.filter_mtype     = tk.StringVar(value="All")
        self.filter_cr        = tk.StringVar(value="All")
        self.filter_msize     = tk.StringVar(value="All")
        self.filter_legendary = tk.BooleanVar(value=False)

        make_dropdown("Type:", self.monster_types, self.filter_mtype, self._apply_monster_filters)
        make_dropdown("CR:",   self.monster_crs,   self.filter_cr,    self._apply_monster_filters)
        make_dropdown("Size:", self.monster_sizes, self.filter_msize, self._apply_monster_filters)

        tk.Checkbutton(filter_bar, text="Legendary only",
                       variable=self.filter_legendary,
                       command=self._apply_monster_filters,
                       font=FONT_SMALL, bg=BG_DARK, fg=GOLD,
                       selectcolor=BG_INPUT,
                       activebackground=BG_DARK).pack(side="left", padx=8)

        tk.Button(filter_bar, text="Reset", font=FONT_SMALL,
                  bg=BG_INPUT, fg=TEXT_DIM, relief="flat", padx=8,
                  command=self._reset_monster_filters).pack(side="left", padx=4)

        self.monster_result_count = tk.Label(filter_bar, text="",
                                             font=FONT_SMALL, bg=BG_DARK, fg=TEXT_DIM)
        self.monster_result_count.pack(side="right", padx=12)

        split = tk.Frame(self.tab_bestiary, bg=BG_DARK)
        split.pack(fill="both", expand=True, pady=(6,0))

        list_frame = tk.Frame(split, bg=BG_CARD,
                              highlightthickness=1, highlightbackground=BORDER)
        list_frame.pack(side="left", fill="both", padx=(0,4))
        list_frame.pack_propagate(False)
        list_frame.configure(width=240)

        list_scroll = ttk.Scrollbar(list_frame, orient="vertical")
        self.monster_listbox = tk.Listbox(list_frame, font=FONT_SMALL,
                                          bg=BG_CARD, fg=TEXT,
                                          selectbackground=GOLD,
                                          selectforeground=BG_DARK,
                                          relief="flat", activestyle="none",
                                          yscrollcommand=list_scroll.set)
        list_scroll.config(command=self.monster_listbox.yview)
        list_scroll.pack(side="right", fill="y")
        self.monster_listbox.pack(fill="both", expand=True)
        self.monster_listbox.bind("<<ListboxSelect>>", self._on_monster_list_select)

        self.monster_card = tk.Frame(split, bg=BG_CARD,
                                     highlightthickness=1,
                                     highlightbackground=BORDER)
        self.monster_card.pack(side="left", fill="both", expand=True)
        tk.Label(self.monster_card,
                 text="✦\n\nSelect a creature from the list",
                 font=FONT_BODY, bg=BG_CARD, fg=TEXT_DIM,
                 justify="center").pack(expand=True)

        self._apply_monster_filters()

    # ── TAB 4: Analytics ──────────────────────────────────
    def _build_analytics_tab(self):
        import matplotlib
        matplotlib.rcParams['figure.facecolor']  = '#1a1a2e'
        matplotlib.rcParams['axes.facecolor']    = '#16213e'
        matplotlib.rcParams['text.color']        = '#e0e0e0'
        matplotlib.rcParams['axes.labelcolor']   = '#e0e0e0'
        matplotlib.rcParams['xtick.color']       = '#e0e0e0'
        matplotlib.rcParams['ytick.color']       = '#e0e0e0'
        matplotlib.rcParams['axes.edgecolor']    = '#444466'
        matplotlib.rcParams['axes.titlecolor']   = '#c9a84c'

        fig = Figure(figsize=(12, 8), dpi=90)
        fig.patch.set_facecolor('#1a1a2e')

        DMG_COLORS = {
            'Fire':'#ff4500','Radiant':'#ffd700','Necrotic':'#9370db',
            'Force':'#00bfff','Lightning':'#7df9ff','Cold':'#add8e6',
            'Psychic':'#ff69b4','Bludgeoning':'#c8a87a','Thunder':'#9370db',
            'Piercing':'#c0c0c0','Acid':'#7fff00','Poison':'#32cd32',
            'Slashing':'#cd853f',
        }

        # chart 1 — effectiveness score
        ax1 = fig.add_subplot(2, 2, 1)
        data   = get_damage_vs_monsters()
        types  = [d["damage_type"] for d in data]
        scores = [d["score"] for d in data]
        colors = [DMG_COLORS.get(t, '#888888') for t in types]
        bars = ax1.barh(types, scores, color=colors)
        ax1.axvline(x=0, color='#888899', linewidth=0.8)
        ax1.set_title("Damage Effectiveness vs Monsters", fontweight="bold")
        ax1.set_xlabel("Score (vulnerable − immune − 0.5×resistant)")
        ax1.invert_yaxis()
        for bar, score in zip(bars, scores):
            x = bar.get_width()
            ax1.text(x + 0.1 if x >= 0 else x - 0.1,
                     bar.get_y() + bar.get_height() / 2,
                     f"{score:.1f}", va='center', fontsize=7,
                     ha='left' if x >= 0 else 'right')

        # chart 2 — immune vs resistant vs vulnerable
        ax2 = fig.add_subplot(2, 2, 2)
        immune    = [d["immune"]     for d in data]
        resistant = [d["resistant"]  for d in data]
        vuln      = [d["vulnerable"] for d in data]
        x = np.arange(len(types))
        w = 0.25
        ax2.bar(x - w, immune,    width=w, label="Immune",     color="#888899")
        ax2.bar(x,     resistant, width=w, label="Resistant",  color="#4169e1")
        ax2.bar(x + w, vuln,      width=w, label="Vulnerable", color="#cc3300")
        ax2.set_xticks(x)
        ax2.set_xticklabels(types, rotation=45, ha='right', fontsize=7)
        ax2.set_title("Monster Defenses by Damage Type", fontweight="bold")
        ax2.legend(fontsize=7, facecolor='#16213e', edgecolor='#444466')

        # chart 3 — spells per school
        ax3 = fig.add_subplot(2, 2, 3)
        school_data = get_school_stats()
        schools     = [r[0] for r in school_data]
        totals      = [r[1] for r in school_data]
        dmg_spells  = [r[3] for r in school_data]
        school_colors = ['#c9a84c','#9370db','#00bfff','#ff4500',
                         '#32cd32','#ff69b4','#add8e6','#ffd700']
        x = np.arange(len(schools))
        ax3.bar(x,     totals,     width=0.4, label="Total spells",  color=school_colors)
        ax3.bar(x,     dmg_spells, width=0.4, label="Damage spells", color='#cc3300', alpha=0.6)
        ax3.set_xticks(x)
        ax3.set_xticklabels(schools, rotation=35, ha='right', fontsize=8)
        ax3.set_title("Spells per School of Magic", fontweight="bold")
        ax3.legend(fontsize=7, facecolor='#16213e', edgecolor='#444466')

        # chart 4 — CR distribution
        ax4 = fig.add_subplot(2, 2, 4)
        cr_data = get_cr_distribution()
        crs     = [str(r[0]) for r in cr_data]
        counts  = [r[1] for r in cr_data]
        ax4.bar(crs, counts, color='#9370db')
        ax4.set_title("Monster CR Distribution (CR 0–10)", fontweight="bold")
        ax4.set_xlabel("Challenge Rating")
        ax4.set_ylabel("Number of Monsters")

        fig.tight_layout(pad=2.0)

        canvas = FigureCanvasTkAgg(fig, master=self.tab_analytics)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    # ── spell filter logic ─────────────────────────────────
    def _apply_spell_filters(self):
        results = filter_spells(
            school=self.filter_school.get(),
            damage_type=self.filter_damage.get(),
            class_=self.filter_class.get(),
            level=self.filter_level.get()
        )
        self.filtered_spells = results
        self.spell_listbox.delete(0, "end")
        for row in results:
            level_str = "C" if row[1] == 0 else str(row[1])
            self.spell_listbox.insert("end", f"  [{level_str}] {row[0]}")
        self.spell_result_count.config(text=f"{len(results)} spells found")

    def _reset_spell_filters(self):
        self.filter_school.set("All")
        self.filter_damage.set("All")
        self.filter_class.set("All")
        self.filter_level.set("All")
        self._apply_spell_filters()

    def _on_spell_list_select(self, event):
        sel = self.spell_listbox.curselection()
        if not sel:
            return
        spell = search_spell(self.filtered_spells[sel[0]][0])
        if spell:
            render_spell_card(self.browse_card, spell)

    # ── monster filter logic ───────────────────────────────
    def _apply_monster_filters(self):
        results = filter_monsters(
            type_=self.filter_mtype.get(),
            cr=self.filter_cr.get(),
            size=self.filter_msize.get(),
            legendary_only=self.filter_legendary.get()
        )
        self.filtered_monsters = results
        self.monster_listbox.delete(0, "end")
        for row in results:
            cr_str = str(int(row[2])) if row[2] == int(row[2]) else str(row[2])
            star = "⭐ " if row[4] else ""
            self.monster_listbox.insert("end", f"  {star}[CR{cr_str}] {row[0]}")
        self.monster_result_count.config(text=f"{len(results)} creatures found")

    def _reset_monster_filters(self):
        self.filter_mtype.set("All")
        self.filter_cr.set("All")
        self.filter_msize.set("All")
        self.filter_legendary.set(False)
        self._apply_monster_filters()

    def _on_monster_list_select(self, event):
        sel = self.monster_listbox.curselection()
        if not sel:
            return
        monster = search_monster(self.filtered_monsters[sel[0]][0])
        if monster:
            render_monster_card(self.monster_card, monster)

    # ── monster search autocomplete ────────────────────────
    def _on_monster_type(self, *args):
        query = self.monster_search_var.get().strip().lower()
        if len(query) < 1:
            self._hide_monster_dropdown()
            return
        matches = [m for m in self.all_monsters if query in m.lower()][:8]
        if matches:
            self.monster_listbox_auto.delete(0, "end")
            for m in matches:
                self.monster_listbox_auto.insert("end", m)
            self.monster_entry.update_idletasks()
            x = self.monster_entry.winfo_rootx() - self.root.winfo_rootx()
            y = self.monster_entry.winfo_rooty() - self.root.winfo_rooty() + self.monster_entry.winfo_height()
            self.monster_dropdown_frame.place(x=x, y=y, width=self.monster_entry.winfo_width())
            self.monster_dropdown_frame.lift()
        else:
            self._hide_monster_dropdown()

    def _focus_monster_dropdown(self):
        if self.monster_listbox_auto.size() > 0:
            self.monster_listbox_auto.focus_set()
            self.monster_listbox_auto.selection_set(0)

    def _select_from_monster_dropdown(self):
        sel = self.monster_listbox_auto.curselection()
        if sel:
            self.monster_search_var.set(self.monster_listbox_auto.get(sel[0]))
            self._hide_monster_dropdown()
            self._do_monster_search()

    def _hide_monster_dropdown(self):
        self.monster_dropdown_frame.place_forget()

    def _do_monster_search(self):
        self._hide_monster_dropdown()
        name = self.monster_search_var.get().strip()
        if not name:
            return
        monster = search_monster(name)
        if monster:
            render_monster_card(self.monster_card, monster)
        else:
            for w in self.monster_card.winfo_children():
                w.destroy()
            tk.Label(self.monster_card,
                     text=f'✦  "{name}" not found in the bestiary  ✦',
                     font=FONT_BODY, bg=BG_CARD, fg=RED).pack(expand=True)

    # ── spell search autocomplete ──────────────────────────
    def _on_type(self, *args):
        query = self.search_var.get().strip().lower()
        if len(query) < 1:
            self._hide_dropdown()
            return
        matches = [s for s in self.all_spells if query in s.lower()][:8]
        if matches:
            self.listbox.delete(0, "end")
            for m in matches:
                self.listbox.insert("end", m)
            self.entry.update_idletasks()
            x = self.entry.winfo_rootx() - self.root.winfo_rootx()
            y = self.entry.winfo_rooty() - self.root.winfo_rooty() + self.entry.winfo_height()
            self.dropdown_frame.place(x=x, y=y, width=self.entry.winfo_width())
            self.dropdown_frame.lift()
        else:
            self._hide_dropdown()

    def _focus_dropdown(self):
        if self.listbox.size() > 0:
            self.listbox.focus_set()
            self.listbox.selection_set(0)

    def _select_from_dropdown(self):
        sel = self.listbox.curselection()
        if sel:
            self.search_var.set(self.listbox.get(sel[0]))
            self._hide_dropdown()
            self._do_search()

    def _hide_dropdown(self):
        self.dropdown_frame.place_forget()

    def _do_search(self):
        self._hide_dropdown()
        name = self.search_var.get().strip()
        if not name:
            return
        spell = search_spell(name)
        if spell:
            render_spell_card(self.card, spell)
        else:
            for w in self.card.winfo_children():
                w.destroy()
            tk.Label(self.card,
                     text=f'✦  "{name}" not found in the tome  ✦',
                     font=FONT_BODY, bg=BG_CARD, fg=RED).pack(expand=True)

# ── entry point ────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = SpellbookApp(root)
    root.mainloop()